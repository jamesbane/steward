# Python
import io
import sys
import time
import datetime
import traceback
from collections import OrderedDict

# Django
from django.utils import timezone

# Application
from tools.models import Process

# Third Party
from lib.pyutil.util import Util
from lib.pybw.broadworks import BroadWorks, Nil


class FraudCompliance():
    _bw = None
    _process = None
    _device_type_cache = dict()

    def __init__(self, process):
        self._bw = BroadWorks(url='http://192.168.151.21/webservice/services/ProvisioningService?wsdl',
                              username='develop', password='W4sz2lZHtk^3W)P4+P2VS#IH=H_xXV$3')
        self._process = process
        self._bw.LoginRequest14sp4()

    def logout(self):
        self._bw.LogoutRequest()

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

    def reset_group(self, provider_id, group_id, level=0):
        content = io.StringIO()
        passwords = io.StringIO()
        content.write('{}Processing Group {}::{}\n'.format('    '*level, provider_id, group_id))
        orig_permissions = OrderedDict([
            ('group', 'Allow'),
            ('local', 'Allow'),
            ('tollFree', 'Allow'),
            ('toll', 'Allow'),
            ('international', 'Disallow'),
            ('operatorAssisted', 'Allow'),
            ('chargeableDirectoryAssisted', 'Allow'),
            ('specialServicesI', 'Allow'),
            ('specialServicesII', 'Allow'),
            ('premiumServicesI', 'Allow'),
            ('premiumServicesII', 'Allow'),
            ('casual', 'Disallow'),
            ('urlDialing', 'Disallow'),
            ('unknown', 'Disallow'),
        ])
        content.write('{}    GroupOutgoingCallingPlanOriginatingModifyListRequest(serviceProviderId={}, groupId={}, origPermissions) >> '.format('    '*level, provider_id, group_id)),
        resp0 = self._bw.GroupOutgoingCallingPlanOriginatingModifyListRequest(provider_id, group_id, groupPermissions=orig_permissions)
        content.write(self.parse_response(resp0, level))
        redirect_permissions = OrderedDict([
            ('group', True),
            ('local', True),
            ('tollFree', True),
            ('toll', True),
            ('international', False),
            ('operatorAssisted', False),
            ('chargeableDirectoryAssisted', False),
            ('specialServicesI', False),
            ('specialServicesII', False),
            ('premiumServicesI', False),
            ('premiumServicesII', False),
            ('casual', False),
            ('urlDialing', False),
            ('unknown', False),
        ])
        content.write('{}    GroupOutgoingCallingPlanRedirectingModifyListRequest(serviceProviderId={}, groupId={}, redirectPermissions) >> '.format('    '*level, provider_id, group_id)),
        resp1 = self._bw.GroupOutgoingCallingPlanRedirectingModifyListRequest(provider_id, group_id, groupPermissions=redirect_permissions)
        content.write(self.parse_response(resp1, level))

        # Reboot phones
        content.write('    {}GroupAccessDeviceGetListRequest({}, {}) '.format('    '*level, provider_id, group_id))
        resp3 = self._bw.GroupAccessDeviceGetListRequest(provider_id, group_id)
        content.write(self.parse_response(resp3, level))
        devices = resp3['data']['accessDeviceTable']
        for device in devices:
            device_name = device['Device Name']
            device_type = device['Device Type']
            content.write('{}GroupAccessDeviceGetUserListRequest({}, {}, {}) '.format('    '*level, provider_id, group_id, device_name))
            resp0 = self._bw.GroupAccessDeviceGetUserListRequest(provider_id, group_id, device_name)
            content.write(self.parse_response(resp0, level))
            line_ports = sorted(resp0['data']['deviceUserTable'], key=lambda k: k['Order'])
            if len(line_ports) > 0 and not FraudCompliance.has_primary_line_port(line_ports):
                line_port = FraudCompliance.get_first_primary_line_port(line_ports)
                if line_port is not None:
                    content.write('{}GroupAccessDeviceModifyUserRequest({}, {}, {}, {}, isPrimaryLinePort={}) '.format('    '*(level+1), provider_id, group_id, device_name, line_port['Line/Port'], True))
                    resp1 = self._bw.GroupAccessDeviceModifyUserRequest(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name, linePort=line_port['Line/Port'], isPrimaryLinePort=True)
                    content.write(self.parse_response(resp1, level))
            # Reboot device
            content.write('{}    GroupAccessDeviceResetRequest(serviceProviderId={}, groupId={}, deviceName={}) >> '.format('    '*level, provider_id, group_id, device_name)),
            resp8 = self._bw.GroupAccessDeviceResetRequest(serviceProviderId=provider_id, groupId=group_id, deviceName=device_name)
            content.write(self.parse_response(resp8, level))


        content.write('{}    UserGetListInGroupRequest(serviceProviderId={}, groupId={}) >> '.format('    '*level, provider_id, group_id)),
        resp2 = self._bw.UserGetListInGroupRequest(serviceProviderId=provider_id, groupId=group_id)
        content.write(self.parse_response(resp2, level))
        users = resp2['data']['userTable']
        for user in users:
            user_id = user['User Id']
            content.write('{}  User {}\n'.format('    '*level, user_id))
            # Outbound calling plan set to group
            content.write('{}    UserOutgoingCallingPlanOriginatingModifyRequest(useCustomSettings=False) >> '.format('    '*level)),
            resp3 = self._bw.UserOutgoingCallingPlanOriginatingModifyRequest(userId=user_id, useCustomSettings=False)
            content.write(self.parse_response(resp3, level))
            # Get devices
            line_ports = list()
            content.write('{}    UserGetRequest19(userId={}) >> '.format('    '*level, user_id)),
            resp4 = self._bw.UserGetRequest19(userId=user_id)
            content.write(self.parse_response(resp4, level))
            user_info = resp4['data']

            # primary device
            if 'accessDeviceEndpoint' in user_info:
                device_name = user_info['accessDeviceEndpoint']['accessDevice']['deviceName']
                device_level = user_info['accessDeviceEndpoint']['accessDevice']['deviceLevel']
                line_port = user_info['accessDeviceEndpoint']['linePort']
                if device_level == 'Group':
                    resp5 = self._bw.GroupAccessDeviceGetRequest18sp1(provider_id, group_id, device_name)
                    device_type = resp5['data']['deviceType']
                elif device_level == 'Service Provider':
                    resp5 = self._bw.ServiceProviderAccessDeviceGetRequest18sp1(provider_id, device_name)
                    device_type = resp5['data']['deviceType']
                if device_type not in self._device_type_cache:
                    resp5 = self._bw.SystemDeviceTypeGetRequest19(device_type)
                    if resp5['data']['deviceTypeConfigurationOption'] in ('Device Management', 'Legacy'):
                        self._device_type_cache[device_type] = True
                    else:
                        self._device_type_cache[device_type] = False
                device_type_dms = self._device_type_cache[device_type]

                line_ports.append({'device_level': device_level,
                                   'device_name': device_name,
                                   'device_type': device_type,
                                   'device_type_dms': device_type_dms,
                                   'line_port': line_port,
                                   'line_port_type': 'Primary'})

            # shared call appearances
            content.write('{}    UserSharedCallAppearanceGetRequest16sp2(userId={}) >> '.format('    '*level, user_id)),
            resp6 = self._bw.UserSharedCallAppearanceGetRequest16sp2(userId=user_id)
            content.write(self.parse_response(resp4, level))
            appearances = resp6['data']['endpointTable']
            for appearance in appearances:
                device_name = appearance['Device Name']
                device_level = appearance['Device Level']
                device_type = appearance['Device Type']
                line_port = appearance['Line/Port']
                if device_type not in self._device_type_cache:
                    resp7 = self._bw.SystemDeviceTypeGetRequest19(device_type)
                    if resp7['data']['deviceTypeConfigurationOption'] in ('Device Management', 'Legacy'):
                        self._device_type_cache[device_type] = True
                    else:
                        self._device_type_cache[device_type] = False
                device_type_dms = self._device_type_cache[device_type]

                line_ports.append({'device_level': device_level,
                                   'device_name': device_name,
                                   'device_type': device_type,
                                   'device_type_dms': device_type_dms,
                                   'line_port': line_port,
                                   'line_port_type': 'Shared'})

            auth_username = '{}_{}'.format(user_id, Util.random_password(length=16, specials=False))
            auth_password = Util.random_password(length=32)
            user_password = Util.random_password(length=32)

            # Reset user passwords
            content.write('{}    UserModifyRequest17sp4(userId={}, newPassword="...") >> '.format('    '*level, user_id, user_password)),
            resp9 = self._bw.UserModifyRequest17sp4(userId=user_id, newPassword=user_password)
            content.write(self.parse_response(resp9, level))

            # Reset sip passwords
            content.write('{}    UserAuthenticationModifyRequest(userId={}, userName={}, newPassword="...") >> '.format('    '*level, user_id, auth_username, auth_password)),
            resp9 = self._bw.UserAuthenticationModifyRequest(userId=user_id, userName=auth_username, newPassword=auth_password)
            content.write(self.parse_response(resp9, level))

            # Line/Port Passwords
            for line_port in line_ports:
                if not line_port['device_type_dms']:
                    passwords.write('"{}","{}","{}","{}","{}","{}","{}","{}"\n'.format(provider_id, group_id, line_port['device_level'], line_port['device_name'], user_id, line_port['line_port'], auth_username, auth_password))

            # Rebuild files
            for line_port in line_ports:
                if line_port['device_level'] == 'Group':
                    content.write('{}    GroupCPEConfigRebuildDeviceConfigFileRequest(serviceProviderId={}, groupId={}, deviceName={}) >> '.format('    '*level, provider_id, group_id, line_port['device_name'])),
                    resp10 = self._bw.GroupCPEConfigRebuildDeviceConfigFileRequest(serviceProviderId=provider_id, groupId=group_id, deviceName=line_port['device_name'])
                    content.write(self.parse_response(resp10, level))
                elif device['device_level'] == 'Service Provider':
                    content.write('{}    ServiceProviderCPEConfigRebuildDeviceConfigFileRequest(serviceProviderId={}, deviceName={}) >> '.format('    '*level, provider_id, line_port['device_name'])),
                    resp10 = self._bw.ServiceProviderCPEConfigRebuildDeviceConfigFileRequest(serviceProviderId=provider_id, deviceName=line_port['device_name'])
                    content.write(self.parse_response(resp10, level))

            # Deactivate intercept user
            content.write('{}    UserInterceptUserModifyRequest16(userId={}, isActive=False) >> '.format('    '*level, user_id)),
            resp11 = self._bw.UserInterceptUserModifyRequest16(userId=user_id, isActive=False)
            content.write(self.parse_response(resp11, level))

        # Deactivate intercept group
        content.write('{}Post Process Group {}::{}\n'.format('    '*level, provider_id, group_id))
        content.write('{}    GroupInterceptGroupModifyRequest16(serviceProviderId={}, groupId={}, isActive=False) >> '.format('    '*level, provider_id, group_id)),
        resp12 = self._bw.GroupInterceptGroupModifyRequest16(serviceProviderId=provider_id, groupId=group_id, isActive=False)
        content.write(self.parse_response(resp12, level))

        rval = {
            'content': content.getvalue(),
            'passwords': passwords.getvalue(),
        }
        content.close()
        passwords.close()
        return rval


def fraud_compliance_reset(process_id):
    process = Process.objects.get(id=process_id)
    try:
        print("Process {}: {} -> {}".format(process_id, process.method, process.parameters))
        process.status = process.STATUS_RUNNING
        process.save(update_fields=['status'])

        fc = FraudCompliance(process=process)
        content = dict()

        # Retrieve Data
        provider_type = process.parameters.get('provider_type', None)
        provider_id = process.parameters.get('provider_id', None)
        group_id = process.parameters.get('group_id', None)

        if provider_id and group_id:
            content_key_name = "log_{}-{}_{}.txt".format(provider_id, group_id, datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
            password_key_name = "passwords_{}-{}_{}.csv".format(provider_id, group_id, datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
        elif provider_id:
            content_key_name = "log_{}_{}.txt".format(provider_id, datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
            password_key_name = "passwords_{}_{}.csv".format(provider_id, datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
        else:
            content_key_name = "log_{}.txt".format(datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
            password_key_name = "passwords_{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))

        file_content = io.StringIO()
        password_content = io.StringIO()
        password_content.write('"{}","{}","{}","{}","{}","{}","{}","{}"\n'.format('Provider Id', 'Group Id', 'Device Level', 'Device Name', 'User Id', 'Line Port', 'Auth Username', 'Auth Password'))

        if provider_id and group_id:
            file_content.write('Group {}::{}\n'.format(provider_id, group_id))
            content[content_key_name] = file_content.getvalue()
            content[password_key_name] = password_content.getvalue()
            process.content = content
            process.save(update_fields=['content'])
            rdata = fc.reset_group(provider_id=provider_id, group_id=group_id, level=1)
            file_content.write(rdata['content'])
            password_content.write(rdata['passwords'])
            content[content_key_name] = file_content.getvalue()
            content[password_key_name] = password_content.getvalue()
            process.content = content
            process.save(update_fields=['content'])
        elif provider_id:
            file_content.write('Provider {}\n'.format(provider_id))
            content[content_key_name] = file_content.getvalue()
            content[password_key_name] = password_content.getvalue()
            process.content = content
            process.save(update_fields=['content'])
            fc.provider_check(provider_id, True if provider_type == 'Enterprise' else False)
            groups = fc.groups(provider_id)
            for group in groups:
                group_id = group['Group Id']
                file_content.write('    Group {}::{}\n'.format(provider_id, group_id))
                content[content_key_name] = file_content.getvalue()
                content[password_key_name] = password_content.getvalue()
                process.content = content
                process.save(update_fields=['content'])
                rdata = fc.reset_group(provider_id=provider_id, group_id=group_id, level=2)
                file_content.write(rdata['content'])
                password_content.write(rdata['passwords'])
                content[content_key_name] = file_content.getvalue()
                content[password_key_name] = password_content.getvalue()
                process.content = content
                process.save(update_fields=['content'])

        content[content_key_name] = file_content.getvalue()
        content[password_key_name] = password_content.getvalue()
        process.content = content
        process.status = process.STATUS_COMPLETED
        process.end_timestamp = timezone.now()
        process.save(update_fields=['content', 'status', 'end_timestamp'])
        file_content.close()
        password_content.close()
        fc.logout()
    except Exception:
        process.status = process.STATUS_ERROR
        process.end_timestamp = timezone.now()
        process.exception = traceback.format_exc()
        process.save(update_fields=['status', 'exception', 'end_timestamp'])
