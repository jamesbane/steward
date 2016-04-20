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


class PttConfigurator():
    _bw = None
    _process = None

    def __init__(self, process):
        self._process = process
        self._bw = BroadWorks(**settings.PLATFORMS['broadworks'])
        self._bw.LoginRequest14sp4()

    def provider_check(self, provider_id, enterprise=False):
        if enterprise:
            resp0 = self._bw.ServiceProviderGetRequest17sp1(provider_id)
            provider_info = resp0['data']
            print(provider_info)
            if 'isEnterprise' in provider_info and provider_info['isEnterprise'] != True:
                raise Exception('Provider Id is not an Enterprise')
            elif 'isEnterprise' not in provider_info:
                raise Exception('Provider Id is not an Enterprise')

    def groups(self, provider_id):
        resp0 = self._bw.GroupGetListInServiceProviderRequest(serviceProviderId=provider_id)
        return resp0['data']['groupTable']

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

    def configure_group(self, provider_id, group_id, level=0):
        log = io.StringIO()
        summary = io.StringIO()

        # Get list of all users...
        log.write('{}UserGetListInGroupRequest({}, {}) '.format('    '*(level+1), provider_id, group_id))
        resp0 = self._bw.UserGetListInGroupRequest(provider_id, group_id)
        log.write(self.parse_response(resp0, level))
        users = resp0['data']['userTable']
        for user in users:
            user_id = user['User Id']
            log.write("{}UserPushToTalkModifyRequest({},  accessListSelection='Allow Calls From Everyone Except Selected Users') ".format('    '*(level+1), user_id))
            resp1 = self._bw.UserPushToTalkModifyRequest(user_id, accessListSelection='Allow Calls From Everyone Except Selected Users')
            log.write('{}\n'.format(resp1['type']))
            if resp1['type'] == 'c:SuccessResponse':
                summary.write('"{}","{}","{}","{}"\n'.format(provider_id, group_id, user_id, 'Success'))

        rval = {'log': log.getvalue(), 'summary': summary.getvalue()}
        log.close()
        summary.close()
        return rval


def ptt_configurator(process_id):
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
        ptt = PttConfigurator(process)

        log = io.StringIO()
        summary = io.StringIO()
        summary.write('"Provider Id","Group Id","User Id","Result"\n')

        # Initial content
        content['log.txt'] = log.getvalue()
        content['summary.csv'] = summary.getvalue()
        process.content = content
        process.save(update_fields=['content'])

        # Determine what to do
        if provider_id and group_id:
            log.write('Group {}::{}\n'.format(provider_id, group_id))
            content['log.txt'] = log.getvalue()
            content['summary.csv'] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
            data = ptt.configure_group(provider_id=provider_id, group_id=group_id, level=1)
            log.write(data['log'])
            summary.write(data['summary'])
            content['log.txt'] = log.getvalue()
            content['summary.csv'] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
        elif provider_id:
            log.write('Provider {}\n'.format(provider_id))
            content['log.txt'] = log.getvalue()
            content['summary.csv'] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
            data = ptt.provider_check(provider_id, True if provider_type == 'Enterprise' else False)
            content['log.txt'] = log.getvalue()
            content['summary.csv'] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
            groups = ptt.groups(provider_id)
            for group in groups:
                group_id = group['Group Id']
                log.write('    Group {}::{}\n'.format(provider_id, group_id))
                content['log.txt'] = log.getvalue()
                content['summary.csv'] = summary.getvalue()
                process.content = content
                process.save(update_fields=['content'])
                data = ptt.configure_group(provider_id=provider_id, group_id=group_id, level=1)
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
