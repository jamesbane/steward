# Python
import io
import sys
import time
import requests
import datetime
import traceback
from collections import OrderedDict

# Django
from django.utils import timezone
from django.conf import settings

# Application
from tools.models import Process

# Third Party
from lib.pyutil.util import Util
from lib.pybw.broadworks import BroadWorks, Nil


class TagRemoval():
    _bw = None
    _process = None
    _tags = None
    _device_types = ['Polycom Soundpoint IP 300', 'Polycom Soundpoint IP 320 330',
                     'Polycom Soundpoint IP 335', 'Polycom Soundpoint IP 4000',
                     'Polycom Soundpoint IP 430', 'Polycom Soundpoint IP 450',
                     'Polycom Soundpoint IP 450 Test', 'Polycom Soundpoint IP 500',
                     'Polycom Soundpoint IP 550', 'Polycom Soundpoint IP 550 test',
                     'Polycom Soundpoint IP 600', 'Polycom Soundpoint IP 601',
                     'Polycom Soundpoint IP 650', 'Polycom Soundpoint IP VVX 1500',
                     'Polycom', 'Polycom_IP335', 'Polycom_IP450', 'Polycom_IP550',
                     'Polycom_IP650', 'Polycom_Test', 'Polycom_VVX101', 'Polycom_VVX201',
                     'Polycom_VVX300', 'Polycom_VVX400', 'Polycom_VVX500', 'Polycom_VVX600',
                     'Polycom-331', 'Polycom-conf', 'PolycomFirmware',]

    def __init__(self, process, tags):
        self._process = process
        self._tags = tags
        self._bw = BroadWorks(**settings.PLATFORMS['broadworks'])
        self._bw.LoginRequest14sp4()

    def parse_response(self, response, level):
        content = io.StringIO()
        content.write('{}\n'.format(response['type']))
        if response['type'] == 'c:ErrorResponse':
            if 'summaryEnglish' in response['data'] and 'errorCode' in response['data']:
                content.write('{}[{}] {}\n'.format('    '*(level+1), response['data']['errorCode'], response['data']['summaryEnglish']))
            elif 'summaryEnglish' in response['data']:
                content.write('{}{}\n'.format('    '*level, response['data']['summaryEnglish']))
            elif 'summary' in response['data'] and 'errorCode' in response['data']:
                content.write('{}[{}] {}\n'.format('    '*(level+1), response['data']['errorCode'], response['data']['summary']))
            elif 'summary' in response['data']:
                content.write('{}{}\n'.format('    '*(level+1), response['data']['summary']))
        rval = content.getvalue()
        content.close()
        return rval

    def provider_check(self, provider_id, enterprise=False):
        if enterprise:
            resp0 = self._bw.ServiceProviderGetRequest17sp1(provider_id)
            provider_info = resp0['data']
            if 'isEnterprise' in provider_info and provider_info['isEnterprise'] != True:
                raise Exception('Provider Id is not an Enterprise')
            elif 'isEnterprise' not in provider_info:
                raise Exception('Provider Id is not an Enterprise')

    def providers(self):
        resp0 = self._bw.ServiceProviderGetListRequest()
        return resp0['data']['serviceProviderTable']

    def groups(self, provider_id):
        resp0 = self._bw.GroupGetListInServiceProviderRequest(serviceProviderId=provider_id)
        return resp0['data']['groupTable']

    def provider_report(self, provider_id, level=0):
        log = io.StringIO()
        summary = io.StringIO()

        rval = {'log': log.getvalue(), 'summary': summary.getvalue()}
        log.close()
        summary.close()
        return rval

    def group_remove_tags(self, provider_id, group_id, level=0):
        log = io.StringIO()
        summary = io.StringIO()

        # Get Devices in Group
        log.write('{}GroupAccessDeviceGetListRequest({}, {}) '.format('    '*(level+1), provider_id, group_id))
        resp1 = self._bw.GroupAccessDeviceGetListRequest(provider_id, group_id)
        log.write(self.parse_response(resp1, level))
        devices = resp1['data']['accessDeviceTable']
        for device in devices:
            device_data = list()
            device_name = device['Device Name']
            resp2 = self._bw.GroupAccessDeviceCustomTagGetListRequest(provider_id, group_id, device_name)
            device_tags = resp2['data']['deviceCustomTagsTable']
            for tag in device_tags:
                tag_name = tag['Tag Name']
                tag_value = tag['Tag Value']
                if tag_name in self._tags:
                    device_data.append(tag_name)
                    resp3 = self._bw.GroupAccessDeviceCustomTagDeleteListRequest(provider_id, group_id, device_name, tagNames=tag_name)
                    break
            if device_data:
                summary.write('"{}","{}","{}","{}"\n'.format(provider_id, group_id, device_name, ", ".join(device_data)))

        rval = {'log': log.getvalue(), 'summary': summary.getvalue()}
        log.close()
        summary.close()
        return rval


def tag_clean(tag_name):
    tag_name = tag_name.strip()
    if not tag_name.startswith('%'):
        tag_name = '%' + tag_name
    if not tag_name.endswith('%'):
        tag_name = tag_name + '%'
    return tag_name


def tag_removal(process_id):
    process = Process.objects.get(id=process_id)
    content = dict()
    try:
        print("Process {}: {} -> {}".format(process_id, process.method, process.parameters))
        process.status = process.STATUS_RUNNING
        process.save(update_fields=['status'])

        # Retrieve Data
        provider_type = process.parameters.get('provider_type', None)
        provider_id = process.parameters.get('provider_id', None)
        group_id = process.parameters.get('group_id', None)
        tags = process.parameters.get('tag_names', None)
        if not tags:
            raise RuntimeError('Tags are Required')
        else:
            tags = [tag_clean(tag) for tag in tags.split(',')]
        tr = TagRemoval(process, tags)

        log = io.StringIO()
        summary = io.StringIO()
        summary.write('"Provider Id","Group Id","Device Name","Removed Tags"\n')

        # Initial content
        content['log.txt'] = log.getvalue()
        content['summary.csv'] = summary.getvalue()
        process.content = content
        process.save(update_fields=['content'])

        # Determine what to do
        if provider_id and group_id:
            data = tr.group_remove_tags(provider_id=provider_id, group_id=group_id)
            log.write(data['log'])
            summary.write(data['summary'])
            content['log.txt'] = log.getvalue()
            content['summary.csv'] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
        elif provider_id:
            tr.provider_check(provider_id, True if provider_type == 'Enterprise' else False)
            groups = tr.groups(provider_id)
            for group in groups:
                group_id = group['Group Id']
                data = tr.group_remove_tags(provider_id=provider_id, group_id=group_id)
                log.write(data['log'])
                summary.write(data['summary'])
                content['log.txt'] = log.getvalue()
                content['summary.csv'] = summary.getvalue()
                process.content = content
                process.save(update_fields=['content'])

        # after things are finished
        content['log.txt'] = log.getvalue()
        content['summary.csv'] = summary.getvalue()
        process.content = content
        process.status = process.STATUS_COMPLETED
        process.end_timestamp = timezone.now()
        process.save(update_fields=['content', 'status', 'end_timestamp'])
    except Exception:
        process.status = process.STATUS_ERROR
        process.end_timestamp = timezone.now()
        process.exception = traceback.format_exc()
        process.save(update_fields=['status', 'exception', 'end_timestamp'])
