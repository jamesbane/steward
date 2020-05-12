# Python
import io
import os
import csv
import sys
import time
import base64
import datetime
import traceback
import string
from io import BytesIO
from collections import OrderedDict
from random import randint, choice, seed

# Django
from django.utils import timezone
from django.conf import settings

# Application
from tools.models import Process, ProcessContent

# Third Party
from lib.pyutil.util import Util
from lib.pybw.broadworks import BroadWorks, Nil
from lxml import etree


class BroadWorksDeviceCreds:
    _bw = None
    _content = io.StringIO()

    def __init__(self, process):
        self._process = process
        self._bw = BroadWorks(url=self._process.platform.uri,
                              username=self._process.platform.username,
                              password=self._process.platform.password)
        self._bw.LoginRequest14sp4()

    @staticmethod
    def has_primary_line_port(device_user_table):
        for line_port in device_user_table:
            if line_port['Primary Line/Port'] == 'true':
                return True
        return False

    @staticmethod
    def get_first_primary_line_port(line_ports):
        for line_port in line_ports:
            if line_port['Endpoint Type'] == 'Primary':
                return line_port
        return None

    def logout(self):
        self._bw.LogoutRequest()

    def parse_response(self, response, level):
        content = io.StringIO()
        content.write('{}\n'.format(response['type']))
        if response['type'] == 'c:ErrorResponse':
            if 'summaryEnglish' in response['data'] and 'errorCode' in response['data']:
                content.write('        {}[{}] {}\n'.format('    '*level, response['data']['errorCode'], response['data']['summaryEnglish']))
            elif 'summaryEnglish' in response['data']:
                content.write('        {}{}\n'.format('    '*level, response['data']['summaryEnglish']))
            elif 'summary' in response['data'] and 'errorCode' in response['data']:
                content.write('        {}[{}] {}\n'.format('    '*level, response['data']['errorCode'], response['data']['summary']))
            elif 'summary' in response['data']:
                content.write('        {}{}\n'.format('    '*level, response['data']['summary']))
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

    def groups(self, provider_id):
        resp0 = self._bw.GroupGetListInServiceProviderRequest(serviceProviderId=provider_id)
        return resp0['data']['groupTable']

    def modify_group_device_creds(self, provider_id, group_id, device_type, **kwargs):
        log = io.StringIO()
        summary = io.StringIO()
        action = kwargs.get('tool_action', 'auth_change')
        level = kwargs.get('level', 0)
        log.write("{}Modify Group Device Credentials: {}::{}::{}\n".format('    '*level, provider_id, group_id, device_type))

        # get devices
        log.write('    {}Devices\n'.format('    '*level))
        log.write('    {}GroupAccessDeviceGetListRequest({}, {}) '.format('    '*(level+1), provider_id, group_id))
        resp3 = self._bw.GroupAccessDeviceGetListRequest(provider_id, group_id)
        log.write(self.parse_response(resp3, level))
        devices = resp3['data']['accessDeviceTable']
        for device in devices:
            device_name = device['Device Name']
                
            if device['Device Type'] == device_type:
                log.write('    {}Device {}::{}::{})\n'.format('    '*(level+1), provider_id, group_id, device_name))
                rdata = self.modify_polycom_credentials(provider_id=provider_id, group_id=group_id, device_name=device_name, device_type=device_type, action=action, level=(level+3))

                log.write(rdata['log'])
                summary.write(rdata['summary'])
            else:
                summary.write('"{}","{}","{}","{}","{}"\n'.format(provider_id, group_id, device_type, device_name, 'Pass'))
        return {'log': log.getvalue(), 'summary': summary.getvalue()}

    def modify_polycom_credentials(self, provider_id, group_id, device_name, device_type, action, **kwargs):
        log = io.StringIO()
        summary = io.StringIO()
        level = kwargs.get('level', 0)
        log.write('{}Modify Polycom Credentials: {}::{}::{} ({})\n'.format('    '*level, provider_id, group_id, device_name, device_type))

        # Retrieve Device Info
        if provider_id and group_id and device_name:
            log.write('{}GroupAccessDeviceGetRequest18sp1({}, {}, {}) '.format('    '*(level+1), provider_id, group_id, device_name))
            resp0 = self._bw.GroupAccessDeviceGetRequest18sp1(provider_id, group_id, device_name)
            log.write(self.parse_response(resp0, level))
            device_info = resp0['data']
        elif provider_id and device_name:
            log.write('{}ServiceProviderAccessDeviceGetRequest18sp1({}, {}) '.format('    '*(level+1), provider_id, device_name))
            resp1 = self._bw.ServiceProviderAccessDeviceGetRequest18sp1(provider_id, device_name)
            log.write(self.parse_response(resp1, level))
            device_info = resp1['data']
        else:
            log.write('{}Could not determine device type for {}:{}:{}, not enough data\n'.format('    '*(level+1), provider_id, group_id, device_name))
            summary.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(provider_id, group_id, device_type, device_name, '', '', 'Could not retrieve device details'))
            return {'log': log.getvalue(), 'summary': summary.getvalue()}

        if action == 'auth_change':
            # New device info if action = auth_change
            size = (16 - (len(device_info['userName']) + 1))
            device_username = device_info['userName'] + '_' + ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(size))
            # seed with the username so we can generate the same pw later 
            seed(device_username)
            device_password = randint(10000000, 99999999) 

            # Load template config file 
            tmpl = etree.parse(settings.BASE_DIR + '/tools/static/phone.cfg.template')
            changeEl = tmpl.find('change')

            # Build Configuration Files
            config_change = '<change device.set="1" device.dhcp.bootSrvUseOpt.set="1" device.dhcp.bootSrvUseOpt="Static" device.prov.user.set="1" device.prov.user="{username}" device.prov.password.set="1" device.prov.password="{password}" device.prov.serverType.set="1" device.prov.serverType="HTTP" device.prov.serverName.set="1" device.prov.serverName="bwdms.cspirefiber.com/dms/PolycomVVX" />'.format(username=device_username, password=device_password)

            newChangeEl = etree.fromstring(config_change)
            # Add attributes from changeEl to the new <change> element
            for key, val in changeEl.attrib.items():
                newChangeEl.set(key, val)

            for i in tmpl.xpath("//phone1"):
                i.replace(changeEl, newChangeEl)

            config_contents = etree.tostring(tmpl)
            custom_redirect_file_base64 = base64.b64encode(config_contents).decode('utf-8')

            # Update device profile description with the new username
            log.write('{}GroupAccessDeviceModifyRequest14({},{},{},{}) '.format('   '*(level+1), provider_id, group_id, device_name, device_username))
            resp3 = self._bw.GroupAccessDeviceModifyRequest14(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name, description=device_username)
            log.write(self.parse_response(resp3, level))

            # Send existing device a new config file to redirect to the new device provisioning url + credentials
            log.write('{}GroupAccessDeviceFileModifyRequest14sp8({}, {}, {}, {}, {}, {}) '.format('    '*(level+1), provider_id, group_id, device_name, 'phone%BWDEVICEID%.cfg', 'Custom', '{...}'))
            resp4 = self._bw.GroupAccessDeviceFileModifyRequest14sp8(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name, fileFormat='phone%BWDEVICEID%.cfg', fileSource='Custom', uploadFile={'fileContent': custom_redirect_file_base64})
            log.write(self.parse_response(resp4, level))

        else:
            if "description" not in device_info:
                return { 'log': '', 'summary': '' }

            device_username = device_info['description']
            seed(device_username)
            device_password = randint(10000000, 99999999)

            # Update device profile description and remove device username
            log.write('{}GroupAccessDeviceModifyRequest14({},{},{}) '.format('   '*(level+1), provider_id, group_id, device_name))
            resp3 = self._bw.GroupAccessDeviceModifyRequest14(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name, description='', username=device_username, password=device_password)
            log.write(self.parse_response(resp3, level))
            
            log.write('{}GroupAccessDeviceFileModifyRequest14sp8({}, {}, {}, {}, {}, {}) '.format('    '*(level+1), provider_id, group_id, device_name, 'phone%BWDEVICEID%.cfg', 'Default', '{...}'))
            resp4 = self._bw.GroupAccessDeviceFileModifyRequest14sp8(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name,fileFormat='phone%BWDEVICEID%.cfg', fileSource='Default')
            log.write(self.parse_response(resp4, level))

        log.write('{}GroupCPEConfigRebuildDeviceConfigFileRequest({}, {}, {}) '.format('    '*(level+1), provider_id, group_id, device_name))
        resp5 = self._bw.GroupCPEConfigRebuildDeviceConfigFileRequest(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name)
        log.write(self.parse_response(resp5, level))
        log.write('{}GroupAccessDeviceResetRequest({}, {}, {}) '.format('    '*(level+1), provider_id, group_id, device_name))
        resp6 = self._bw.GroupAccessDeviceResetRequest(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name)
        log.write(self.parse_response(resp6, level))

        # Success!
        log.write('{}Migrated Device {}::{}::{} with UserAgent of {}\n'.format('    '*(level+1), provider_id, group_id, device_name, device_info.get('version', 'Unknown')))
        summary.write('"{}","{}","{}","{}","{}"\n'.format(provider_id, group_id, device_type, device_name, "Success"))
        return {'log': log.getvalue(), 'summary': summary.getvalue()}


def device_creds_modify(process_id):
    process = Process.objects.get(id=process_id)

    # Summary Tab
    summary_content = ProcessContent.objects.create(process=process, tab='Summary', priority=1)
    dir_path = os.path.join(settings.PROTECTED_ROOT, 'process')
    filename_html = '{}_{}'.format(process.id, 'summary.html')
    pathname_html = os.path.join(dir_path, filename_html)
    filename_raw = '{}_{}'.format(process.id, 'summary.csv')
    pathname_raw = os.path.join(dir_path, filename_raw)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    summary_html = open(pathname_html, "w")
    summary_content.html.name = os.path.join('process', filename_html)
    summary_raw = open(pathname_raw, "w")
    summary_content.raw.name = os.path.join('process', filename_raw)
    summary_content.save()

    # Log Tab
    log_content = ProcessContent.objects.create(process=process, tab='Log', priority=2)
    dir_path = os.path.join(settings.PROTECTED_ROOT, 'process')
    filename_raw = '{}_{}'.format(process.id, 'log.txt')
    pathname_raw = os.path.join(dir_path, filename_raw)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    log_raw = open(pathname_raw, "w")
    log_content.raw.name = os.path.join('process', filename_raw)
    log_content.save()

    try:
        print("Process {}: {} -> {}".format(process_id, process.method, process.parameters))
        process.status = process.STATUS_RUNNING
        process.save(update_fields=['status'])

        dm = BroadWorksDeviceCreds(process=process)
        content = dict()

        # Retrieve Data
        provider_type = process.parameters.get('provider_type', None)
        provider_id = process.parameters.get('provider_id', None)
        group_id = process.parameters.get('group_id', None)
        device_type = process.parameters.get('device_type', None)
        tool_action = process.parameters.get('tool_action', 'auth_change')


        # Initial content
        summary_html.write('<table class="table table-striped table-bordered table-hover">\n')
        summary_html.write('<tr>\n')
        summary_html.write('\t<th>Provider Id</th><th>Group Id</th><th>Device Type</th><th>Device Id</th><th>Status</th>\n')
        summary_html.write('</tr>\n')
        summary_html.write('<tbody>\n')
        summary_raw.write('"Provider Id","Group Id","Device Type","Device Id","Status"\n')

        if provider_id and group_id:
            log_raw.write('Group {}::{}\n'.format(provider_id, group_id))
            data = dm.modify_group_device_creds(provider_id=provider_id, group_id=group_id, device_type=device_type, tool_action=tool_action)
            log_raw.write(data['log'])
            summary_raw.write(data['summary'])
            for row in csv.reader(data['summary'].split('\n')):
                if row:
                    summary_html.write('<tr>\n\t')
                    for d in row:
                        summary_html.write('<td>{}</td>'.format(d))
                    summary_html.write('\n</tr>\n')
        #elif
        #    raise Exception('Provider Id and Group Id must be supplied.')

        # after things are finished
        # end html
        summary_html.write('</tbody>\n')
        summary_html.write('</table>\n')
        # save data
        process.status = process.STATUS_COMPLETED
        process.end_timestamp = timezone.now()
        process.save(update_fields=['status', 'end_timestamp'])
        dm.logout()
    except Exception:
        process.status = process.STATUS_ERROR
        process.end_timestamp = timezone.now()
        process.exception = traceback.format_exc()
        process.save(update_fields=['status', 'exception', 'end_timestamp'])

    # Cleanup
    log_raw.close()
    summary_html.close()
    summary_raw.close()
