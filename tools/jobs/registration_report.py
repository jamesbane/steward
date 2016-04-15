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
from lib.pypalladion.palladion import Palladion


class RegistrationReport:
    _palladion = None
    _pl_devices = None
    _bw = None
    _process = None

    def __init__(self, process):
        self._process = process
        self._palladion = Palladion(**settings.PLATFORMS['palladion'])
        self._pl_devices = { x['id']: x for x in self._palladion.devices() }
        requests.packages.urllib3.disable_warnings()
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

    def groups(self, provider_id):
        resp0 = self._bw.GroupGetListInServiceProviderRequest(serviceProviderId=provider_id)
        return resp0['data']['groupTable']

    def group_report(self, provider_id, group_id, level=0):
        log = io.StringIO()
        summary = io.StringIO()

        log.write('{}GroupAccessDeviceGetListRequest({}, {}) '.format('    '*level, provider_id, group_id))
        resp0 = self._bw.GroupAccessDeviceGetListRequest(provider_id, group_id)
        log.write(self.parse_response(resp0, level))
        devices = resp0['data']['accessDeviceTable']
        for device in devices:
            device_name = device['Device Name']
            device_type = device['Device Type']
            log.write('{}Device: {}::{}::{}\n'.format('    '*level, provider_id, group_id, device_name))
            log.write('{}GroupAccessDeviceGetUserListRequest({}, {}, {}) '.format('    '*(level+1), provider_id, group_id, device_name))
            resp1 = self._bw.GroupAccessDeviceGetUserListRequest(provider_id, group_id, device_name)
            log.write(self.parse_response(resp1, level))
            if 'deviceUserTable' in resp1['data'] and len(resp1['data']['deviceUserTable']) > 0:
                line_ports = sorted(resp1['data']['deviceUserTable'], key=lambda k: "None" if k['Order'] is None else k['Order'])
                for line_port in line_ports:
                    user_line_id = line_port['Line/Port'].split('@')[0]
                    log.write('{}{} :: '.format('    '*(level+2), user_line_id))
                    registrars = list()
                    registrations = sorted(self._palladion.registrations(user_line_id), key=lambda reg: reg['dev_id'])
                    for registration in registrations:
                        registrar_name = "???"
                        if registration['dev_id'] in self._pl_devices:
                            registrar_name = self._pl_devices[registration['dev_id']]['name']
                        registrars.append(registrar_name)
                    if len(registrars) > 0:
                        log.write('{}\n'.format('Registered'))
                        summary.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(provider_id, group_id, device_name, device_type, user_line_id, 'Registered', ','.join(registrars)))
                    else:
                        log.write('{}\n'.format('Not Registered'))
                        summary.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(provider_id, group_id, device_name, device_type, user_line_id, 'Not Registered', ''))

        return {'log': log.getvalue(), 'summary': summary.getvalue()}

def registration_report(process_id):
    process = Process.objects.get(id=process_id)
    try:
        print("Process {}: {} -> {}".format(process_id, process.method, process.parameters))
        process.status = process.STATUS_RUNNING
        process.save(update_fields=['status'])

        rp = RegistrationReport(process=process)

        # Retrieve Data
        provider_type = process.parameters.get('provider_type', None)
        provider_id = process.parameters.get('provider_id', None)
        group_id = process.parameters.get('group_id', None)

        content = dict()
        log = io.StringIO()
        summary = io.StringIO()
        log_key_name = 'log.txt'
        summary_key_name = 'summary.csv'
        summary.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format('Provider Id', 'Group Id', 'Device Name', 'Device Type', 'Line/Port', 'Status', 'Proxy/Registrar'))

        if provider_id and group_id:
            log.write('Group {}::{}\n'.format(provider_id, group_id))
            content[log_key_name] = log.getvalue()
            content[summary_key_name] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
            rdata = rp.group_report(provider_id=provider_id, group_id=group_id, level=1)
            log.write(rdata['log'])
            summary.write(rdata['summary'])
            content[log_key_name] = log.getvalue()
            content[summary_key_name] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
        elif provider_id:
            log.write('Provider {}\n'.format(provider_id))
            content[log_key_name] = log.getvalue()
            content[summary_key_name] = summary.getvalue()
            process.content = content
            process.save(update_fields=['content'])
            groups = rp.groups(provider_id)
            for group in groups:
                group_id = group['Group Id']
                log.write('    Group {}::{}\n'.format(provider_id, group_id))
                content[log_key_name] = log.getvalue()
                content[summary_key_name] = summary.getvalue()
                process.content = content
                process.save(update_fields=['content'])
                rdata = rp.group_report(provider_id=provider_id, group_id=group_id, level=2)
                log.write(rdata['log'])
                summary.write(rdata['summary'])
                content[log_key_name] = log.getvalue()
                content[summary_key_name] = summary.getvalue()
                process.content = content
                process.save(update_fields=['content'])

        content[log_key_name] = log.getvalue()
        content[summary_key_name] = summary.getvalue()
        process.content = content
        process.status = process.STATUS_COMPLETED
        process.end_timestamp = timezone.now()
        process.save(update_fields=['content', 'status', 'end_timestamp'])
        log.close()
        summary.close()
    except Exception:
        process.status = process.STATUS_ERROR
        process.end_timestamp = timezone.now()
        process.exception = traceback.format_exc()
        process.save(update_fields=['status', 'exception', 'end_timestamp'])
