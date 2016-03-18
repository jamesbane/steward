# Python
import io
import re
import sys
import time
import base64
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



class BroadWorksLab:
    _bw = None
    _content = io.StringIO()

    def __init__(self, process):
        self._bw = BroadWorks(url='http://192.168.151.21/webservice/services/ProvisioningService?wsdl',
                              username='develop', password='W4sz2lZHtk^3W)P4+P2VS#IH=H_xXV$3')
        self._process = process
        self._bw.LoginRequest14sp4()

    def status(self, provider, groups, users):
        for user in users:
            device_provider_id = provider['id']
            device_group_id = user['group_id']
            device_name = user['user_id']

            device_user_agent = None
            device_registered = False
            device_uri = None
            resp6 = self._bw.UserGetRegistrationListRequest(user['user_id'])
            registrations = resp6['data']['registrationTable']
            for reg in registrations:
                if reg['Device Name'] == device_name:
                    device_user_agent = reg['User Agent']
                    device_registered = True
                    device_uri = reg['URI']
                    break
            self._content.write('Provider: {:<30} Group: {:<15} User: {:<20} Status: {}\n'.format(provider['id'], user['group_id'], user['user_id'], 'Registered' if device_registered else '* Offline *'))

    def rebuild(self, provider, groups, users):
        self._content.write("Reset Existing Devices\n")
        for user in users:
            self._content.write("    GroupAccessDeviceResetRequest(serviceProviderId={}, groupId={}, deviceName={}) ".format(provider['id'], user['group_id'], user['user_id'])),
            resp = self._bw.GroupAccessDeviceResetRequest(serviceProviderId=provider['id'], groupId=user['group_id'], deviceName=user['user_id'])
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
        self._content.write('\n')

        self._content.write("Retrieve Defaults\n")
        self._content.write("    ServiceProviderServiceGetAuthorizationListRequest('LokiHelper') "),
        resp = self._bw.ServiceProviderServiceGetAuthorizationListRequest('LokiHelper')
        loki_service_authorization_list = resp['data']
        self._content.write('{}\n'.format(resp['type']))
        if resp['type'] == 'c:ErrorResponse':
            self._content.write('        {}\n'.format(resp['data']['summary']))
        self._content.write("    GroupServiceGetAuthorizationListRequest('LokiHelper', 'IP Voice Phone System') "),
        resp = self._bw.GroupServiceGetAuthorizationListRequest('LokiHelper', 'IP Voice Phone System')
        loki_group_service_auth = resp['data']
        self._content.write('{}\n'.format(resp['type']))
        if resp['type'] == 'c:ErrorResponse':
            self._content.write('        {}\n'.format(resp['data']['summary']))
        self._content.write('\n')

        self._content.write("Delete Groups & Provider\n")
        for group in groups:
            self._content.write("    GroupDeleteRequest({}, {}) ".format(provider['id'], group['id'])),
            resp = self._bw.GroupDeleteRequest(provider['id'], group['id'])
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
        self._content.write("    ServiceProviderDeleteRequest({}) ".format(provider['id'])),
        resp = self._bw.ServiceProviderDeleteRequest(provider['id'])
        self._content.write('{}\n'.format(resp['type']))
        if resp['type'] == 'c:ErrorResponse':
            self._content.write('        {}\n'.format(resp['data']['summary']))
        self._content.write('\n')

        self._content.write("Enterprise: {}\n".format(provider['id']))
        # Enterprise
        self._content.write("    ServiceProviderAddRequest13mp2({}, {}, enterprise=True) ".format(provider['id'], provider['description'])),
        resp = self._bw.ServiceProviderAddRequest13mp2(provider['id'], provider['description'], enterprise=True)
        self._content.write('{}\n'.format(resp['type']))
        if resp['type'] == 'c:ErrorResponse':
            self._content.write('        {}\n'.format(resp['data']['summary']))
        # assign numbers
        self._content.write("    ServiceProviderDnAddListRequest({}, phoneNumber={{...}}) ".format(provider['id'])),
        resp = self._bw.ServiceProviderDnAddListRequest(provider['id'], phoneNumber=provider['numbers'])
        self._content.write('{}\n'.format(resp['type']))
        if resp['type'] == 'c:ErrorResponse':
            self._content.write('        {}\n'.format(resp['data']['summary']))
        # authorized services
        authorization_list = {'groupServiceAuthorization': list(), 'userServiceAuthorization': list()}
        for d in loki_service_authorization_list['groupServicesAuthorizationTable']:
            if d['Authorized'] != 'true':
                continue
            data = OrderedDict()
            data['serviceName'] = d['Service Name']
            if d['Limited'] == 'Unlimited':
                data['authorizedQuantity'] = {'unlimited': True}
            else:
                data['authorizedQuantity'] = {'quantity': d['Quantity']}
            authorization_list['groupServiceAuthorization'].append(data)
        for d in loki_service_authorization_list['userServicesAuthorizationTable']:
            if d['Authorized'] != 'true':
                continue
            data = OrderedDict()
            data['serviceName'] = d['Service Name']
            if d['Limited'] == 'Unlimited':
                data['authorizedQuantity'] = {'unlimited': True}
            else:
                data['authorizedQuantity'] = {'quantity': d['Quantity']}
            authorization_list['userServiceAuthorization'].append(data)
        self._content.write("    ServiceProviderServiceModifyAuthorizationListRequest({}, ...) ".format(provider['id'])),
        resp = self._bw.ServiceProviderServiceModifyAuthorizationListRequest(provider['id'], **authorization_list)
        self._content.write('{}\n'.format(resp['type']))
        if resp['type'] == 'c:ErrorResponse':
            self._content.write('        {}\n'.format(resp['data']['summary']))

        # service packs
        self._content.write("    ServiceProviderServicePackGetListRequest('LokiHelper') "),
        resp = self._bw.ServiceProviderServicePackGetListRequest('LokiHelper')
        loki_service_pack_list = resp['data']['servicePackName']
        self._content.write('{}\n'.format(resp['type']))
        if resp['type'] == 'c:ErrorResponse':
            self._content.write('        {}\n'.format(resp['data']['summary']))
        for service_pack_name in loki_service_pack_list:
            self._content.write("    ServiceProviderServicePackGetDetailListRequest('LokiHelper', {}) ".format(service_pack_name)),
            resp = self._bw.ServiceProviderServicePackGetDetailListRequest('LokiHelper', service_pack_name)
            service_pack_detail = resp['data']
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))

            services = list()
            for service in service_pack_detail['userServiceTable']:
                # "Service", "Authorized" "Allocated" and "Available".
                services.append(service['Service'])

            self._content.write("    ServiceProviderServicePackAddRequest({}, {}, ...) ".format(provider['id'], service_pack_name)),
            resp = self._bw.ServiceProviderServicePackAddRequest(provider['id'],
                                                                 service_pack_detail['servicePackName'],
                                                                 service_pack_detail['isAvailableForUse'],
                                                                 service_pack_detail['servicePackQuantity'],
                                                                 serviceName=services)
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
        self._content.write('\n')

        for group in groups:
            self._content.write("Group: {}::{}\n".format(provider['id'], group['id']))
            self._content.write("    GroupAddRequest({}, {}, userLimit='999999', groupName={}) ".format(provider['id'], group['id'], group['name'])),
            resp = self._bw.GroupAddRequest(provider['id'], group['id'], userLimit='999999', groupName=group['name'])
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
            self._content.write("    GroupDnAssignListRequest({}, {}, phoneNumber={{...}}) ".format(provider['id'], group['id'])),
            resp = self._bw.GroupDnAssignListRequest(provider['id'], group['id'], phoneNumber=group['numbers'])
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
            self._content.write("    GroupModifyRequest({}, {}, callingLineIdPhoneNumber={}) ".format(provider['id'], group['id'], group['number'])),
            resp = self._bw.GroupModifyRequest(provider['id'], group['id'], callingLineIdPhoneNumber=group['number'])
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
            service_auth = {'servicePackAuthorization': list(), 'groupServiceAuthorization': list(), 'userServiceAuthorization': list()}
            for d in loki_group_service_auth['servicePacksAuthorizationTable']:
                if d['Authorized'] != 'true':
                    continue
                data = OrderedDict()
                data['servicePackName'] = d['Service Pack Name']
                if d['Allowed'] == 'Unlimited':
                    data['authorizedQuantity'] = {'unlimited': True}
                else:
                    data['authorizedQuantity'] = {'quantity': d['Quantity']}
                service_auth['servicePackAuthorization'].append(data)
            for d in loki_group_service_auth['groupServicesAuthorizationTable']:
                if d['Authorized'] != 'true':
                    continue
                data = OrderedDict()
                data['serviceName'] = d['Service Name']
                if d['Allowed'] == 'Unlimited':
                    data['authorizedQuantity'] = {'unlimited': True}
                else:
                    data['authorizedQuantity'] = {'quantity': d['Quantity']}
                service_auth['groupServiceAuthorization'].append(data)
            for d in loki_group_service_auth['userServicesAuthorizationTable']:
                if d['Authorized'] != 'true':
                    continue
                data = OrderedDict()
                data['serviceName'] = d['Service Name']
                if d['Allowed'] == 'Unlimited':
                    data['authorizedQuantity'] = {'unlimited': True}
                else:
                    data['authorizedQuantity'] = {'quantity': d['Quantity']}
                service_auth['userServiceAuthorization'].append(data)

            self._content.write("    GroupServiceModifyAuthorizationListRequest({}, {}, ...) ".format(provider['id'], group['id'])),
            resp = self._bw.GroupServiceModifyAuthorizationListRequest(provider['id'], group['id'], **service_auth)
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
            for service_name in group['assigned_services']:
                self._content.write("    GroupServiceAssignListRequest({}, {}, {}) ".format(provider['id'], group['id'], service_name)),
                resp = self._bw.GroupServiceAssignListRequest(provider['id'], group['id'], service_name)
                self._content.write('{}\n'.format(resp['type']))
                if resp['type'] == 'c:ErrorResponse':
                    self._content.write('        {}\n'.format(resp['data']['summary']))
            orig_permissions = OrderedDict()
            orig_permissions['group'] = 'Allow'
            orig_permissions['local'] = 'Allow'
            orig_permissions['tollFree'] = 'Allow'
            orig_permissions['toll'] = 'Allow'
            orig_permissions['international'] = 'Disallow'
            orig_permissions['operatorAssisted'] = 'Allow'
            orig_permissions['chargeableDirectoryAssisted'] = 'Allow'
            orig_permissions['specialServicesI'] = 'Allow'
            orig_permissions['specialServicesII'] = 'Allow'
            orig_permissions['premiumServicesI'] = 'Allow'
            orig_permissions['premiumServicesII'] = 'Allow'
            orig_permissions['casual'] = 'Disallow'
            orig_permissions['urlDialing'] = 'Disallow'
            orig_permissions['unknown'] = 'Disallow'
            self._content.write("    GroupOutgoingCallingPlanOriginatingModifyListRequest({}, {}, groupPermissions={{...}}) ".format(provider['id'], group['id'])),
            resp = self._bw.GroupOutgoingCallingPlanOriginatingModifyListRequest(provider['id'], group['id'], groupPermissions=orig_permissions)
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
            redirect_permissions = OrderedDict()
            redirect_permissions['group'] = True
            redirect_permissions['local'] = True
            redirect_permissions['tollFree'] = True
            redirect_permissions['toll'] = True
            redirect_permissions['international'] = False
            redirect_permissions['operatorAssisted'] = False
            redirect_permissions['chargeableDirectoryAssisted'] = False
            redirect_permissions['specialServicesI'] = False
            redirect_permissions['specialServicesII'] = False
            redirect_permissions['premiumServicesI'] = False
            redirect_permissions['premiumServicesII'] = False
            redirect_permissions['casual'] = False
            redirect_permissions['urlDialing'] = False
            redirect_permissions['unknown'] = False
            self._content.write("    GroupOutgoingCallingPlanRedirectingModifyListRequest({}, {}, groupPermissions={{...}}) ".format(provider['id'], group['id'])),
            resp = self._bw.GroupOutgoingCallingPlanRedirectingModifyListRequest(provider['id'], group['id'], groupPermissions=redirect_permissions)
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('        {}\n'.format(resp['data']['summary']))
            self._content.write('\n')

        for user in users:
            self._content.write("    {}::{}: {}\n".format(user['group_id'], user['user_id'], user['device_type']))
            self._content.write("        GroupAccessDeviceAddRequest14({}, {}, {}, {}, username={}, password='8675309') ".format(provider['id'], user['group_id'], user['user_id'], user['device_type'], user['device_username'])),
            resp = self._bw.GroupAccessDeviceAddRequest14(provider['id'], user['group_id'], user['user_id'], user['device_type'], username=user['device_username'], password='8675309')
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('            {}\n'.format(resp['data']['summary']))
            access_device_endpoint = OrderedDict()
            access_device_endpoint['accessDevice'] = OrderedDict()
            access_device_endpoint['accessDevice']['deviceLevel'] = 'Group'
            access_device_endpoint['accessDevice']['deviceName'] = user['user_id']
            access_device_endpoint['linePort'] = user['line_port']
            self._content.write("        UserAddRequest17sp4({}, {}, {}, {}, {}, {}, {}, extension={}, password='1234aB!', accessDeviceEndpoint={{...}}) ".format(provider['id'], user['group_id'], user['user_id'], user['last_name'], user['first_name'], user['last_name'], user['first_name'], user['extension'])),
            resp = self._bw.UserAddRequest17sp4(provider['id'], user['group_id'], user['user_id'], user['last_name'], user['first_name'], user['last_name'], user['first_name'], extension=user['extension'], password='1234aB!', accessDeviceEndpoint=access_device_endpoint)
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('            {}\n'.format(resp['data']['summary']))
            self._content.write("        GroupAccessDeviceModifyUserRequest({}, {}, {}, {}, True) ".format(provider['id'], user['group_id'], user['user_id'], user['line_port'])),
            resp = self._bw.GroupAccessDeviceModifyUserRequest(provider['id'], user['group_id'], user['user_id'], user['line_port'], True)
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('            {}\n'.format(resp['data']['summary']))
            self._content.write("        UserServiceAssignListRequest({}, servicePackName={}) ".format(user['user_id'], user['service_pack'])),
            resp = self._bw.UserServiceAssignListRequest(user['user_id'], servicePackName=user['service_pack'])
            self._content.write('{}\n'.format(resp['type']))
            if resp['type'] == 'c:ErrorResponse':
                self._content.write('            {}\n'.format(resp['data']['summary']))
            self._content.write('\n')

        # Shared Call and BLF
        self._content.write("    Shared Call Appearances and Busy Lamp Field\n")
        for user in users:
            # SCA
            for appearance in user['appearances']:
                access_device_endpoint = OrderedDict()
                access_device_endpoint['accessDevice'] = OrderedDict()
                access_device_endpoint['accessDevice']['deviceLevel'] = 'Group'
                access_device_endpoint['accessDevice']['deviceName'] = user['user_id']
                access_device_endpoint['linePort'] = appearance['line_port']
                self._content.write("        UserSharedCallAppearanceAddEndpointRequest14sp2({}, {{...}}, isActive=True, allowOrigination=True, allowTermination=True) ".format(appearance['user_id'])),
                resp = self._bw.UserSharedCallAppearanceAddEndpointRequest14sp2(appearance['user_id'], access_device_endpoint, isActive=True, allowOrigination=True, allowTermination=True)
                self._content.write('{}\n'.format(resp['type']))
                if resp['type'] == 'c:ErrorResponse':
                    self._content.write('            {}\n'.format(resp['data']['summary']))

            # BLF
            if len(user['busy_lamp_field_users']):
                self._content.write("        UserBusyLampFieldModifyRequest({}, listURI={}, monitoredUserIdList={{...}}) ".format(user['user_id'], '{}@telapexinc.com'.format(user['user_id']))),
                resp = self._bw.UserBusyLampFieldModifyRequest(user['user_id'], listURI='{}@telapexinc.com'.format(user['user_id']), monitoredUserIdList=user['busy_lamp_field_users'])
                self._content.write('{}\n'.format(resp['type']))
                if resp['type'] == 'c:ErrorResponse':
                    self._content.write('            {}\n'.format(resp['data']['summary']))
        self._content.write('\n')

        # Group Services
        self._content.write("Group Services\n")
        for group in groups:
            for service in group['service_instances']:
                if service['type'] == 'Hunt Group':
                    service_instance_profile = OrderedDict()
                    service_instance_profile['name'] = service['name']
                    service_instance_profile['callingLineIdLastName'] = service['clid_last_name']
                    service_instance_profile['callingLineIdFirstName'] = service['clid_first_name']
                    service_instance_profile['phoneNumber'] = service['number']
                    service_instance_profile['extension'] = service['extension']
                    service_instance_profile['password'] = '1234aB!'
                    service_instance_profile['callingLineIdPhoneNumber'] = service['clid_number']
                    self._content.write("    GroupHuntGroupAddInstanceRequest19({}, {}, {}, ...) ".format(provider['id'], group['id'], service['user_id'])),
                    resp = self._bw.GroupHuntGroupAddInstanceRequest19(provider['id'], group['id'], service['user_id'], service_instance_profile,
                                                                       policy='Simultaneous', huntAfterNoAnswer=False, noAnswerNumberOfRings=10, forwardAfterTimeout=False,
                                                                       forwardTimeoutSeconds=0, allowCallWaitingForAgents=False, useSystemHuntGroupCLIDSetting=True,
                                                                       includeHuntGroupNameInCLID=False, enableNotReachableForwarding=False, makeBusyWhenNotReachable=True,
                                                                       allowMembersToControlGroupBusy=False, enableGroupBusy=False, agentUserId=service['members'])
                    self._content.write('{}\n'.format(resp['type']))
                    if resp['type'] == 'c:ErrorResponse':
                        self._content.write('            {}\n'.format(resp['data']['summary']))
        self._content.write('\n')


#
# Local variables
#

provider = {
    'id': 'IP_Voice_Engineering_Lab',
    'description': 'IP Voice Engineering Lab',
    'numbers': [
        '+1-251-555-1100', '+1-251-555-1101', '+1-251-555-1102',
        '+1-251-555-1103', '+1-251-555-1104', '+1-251-555-1105',
        '+1-251-555-1106', '+1-251-555-1107', '+1-251-555-1108',
        '+1-251-555-1109',
        '+1-251-555-2100', '+1-251-555-2101', '+1-251-555-2102',
        '+1-251-555-2103', '+1-251-555-2104', '+1-251-555-2105',
        '+1-251-555-2106', '+1-251-555-2107', '+1-251-555-2108',
        '+1-251-555-2109',
    ],
}
groups = [
    {
        'id': 'IPVE_LAB1',
        'name': 'IP Voice Engineering Lab 1',
        'number': '+1-251-555-1100',
        'numbers': [
            '+1-251-555-1100', '+1-251-555-1101', '+1-251-555-1102',
            '+1-251-555-1103', '+1-251-555-1104', '+1-251-555-1105',
            '+1-251-555-1106', '+1-251-555-1107', '+1-251-555-1108',
            '+1-251-555-1109',
        ],
        'assigned_services': ['Outgoing Calling Plan', 'Hunt Group'],
        'service_instances': [
            {
                'type': 'Hunt Group',
                'user_id': '12515551100@telapexinc.com',
                'number': '+1-251-555-1100',
                'extension': '1100',
                'name': 'Lab 1 Main Huntgroup',
                'clid_number': '+1-251-555-1100',
                'clid_last_name': 'Lab 1',
                'clid_first_name': 'Main Huntgroup',
                'members': [
                    'IPVE_LAB1_1001', 'IPVE_LAB1_1002', 'IPVE_LAB1_1003',
                    'IPVE_LAB1_1004', 'IPVE_LAB1_1005', 'IPVE_LAB1_1006',
                    'IPVE_LAB1_1007', 'IPVE_LAB1_1008', 'IPVE_LAB1_1009',
                    'IPVE_LAB1_1010',
                ],
            }
        ]
    },
    {
        'id': 'IPVE_LAB2',
        'name': 'IP Voice Engineering Lab 2',
        'number': '+1-251-555-2100',
        'numbers': [
            '+1-251-555-2100', '+1-251-555-2101', '+1-251-555-2102',
            '+1-251-555-2103', '+1-251-555-2104', '+1-251-555-2105',
            '+1-251-555-2106', '+1-251-555-2107', '+1-251-555-2108',
            '+1-251-555-2109',
        ],
        'assigned_services': ['Outgoing Calling Plan', 'Hunt Group'],
        'service_instances': [
            {
                'type': 'Hunt Group',
                'user_id': '12515552100@telapexinc.com',
                'number': '+1-251-555-2100',
                'extension': '2100',
                'name': 'Lab 2 Main Huntgroup',
                'clid_number': '+1-251-555-2100',
                'clid_last_name': 'Lab 2',
                'clid_first_name': 'Main Huntgroup',
                'members': [
                    'IPVE_LAB2_2001', 'IPVE_LAB2_2002', 'IPVE_LAB2_2003',
                    'IPVE_LAB2_2004', 'IPVE_LAB2_2005', 'IPVE_LAB2_2006',
                    'IPVE_LAB2_2007', 'IPVE_LAB2_2008', 'IPVE_LAB2_2009',
                    'IPVE_LAB2_2010',
                ],
            }
        ]
    }
]
users = [
    # Group 1
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1001',
        'device_type': 'Polycom_VVX300',
        'device_username': 'IPVE-1001',
        'first_name': 'IPVE Lab',
        'last_name': '1001',
        'extension': '1001',
        'line_port': 'IPVE_LAB1_1001@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1002', 'line_port': 'IPVE_LAB1_1001_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1003', 'line_port': 'IPVE_LAB1_1001_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1004', 'IPVE_LAB1_1005', 'IPVE_LAB1_1006',
                                  'IPVE_LAB1_1007', 'IPVE_LAB1_1008', 'IPVE_LAB1_1009',
                                  'IPVE_LAB1_1010'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1002',
        'device_type': 'Polycom_VVX300',
        'device_username': 'IPVE-1002',
        'first_name': 'IPVE Lab',
        'last_name': '1002',
        'extension': '1002',
        'line_port': 'IPVE_LAB1_1002@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1003', 'line_port': 'IPVE_LAB1_1002_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1004', 'line_port': 'IPVE_LAB1_1002_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1001', 'IPVE_LAB1_1005', 'IPVE_LAB1_1006',
                                  'IPVE_LAB1_1007', 'IPVE_LAB1_1008', 'IPVE_LAB1_1009',
                                  'IPVE_LAB1_1010'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1003',
        'device_type': 'Polycom_VVX400',
        'device_username': 'IPVE-1003',
        'first_name': 'IPVE Lab',
        'last_name': '1003',
        'extension': '1003',
        'line_port': 'IPVE_LAB1_1003@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1004', 'line_port': 'IPVE_LAB1_1003_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1005', 'line_port': 'IPVE_LAB1_1003_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1001', 'IPVE_LAB1_1002', 'IPVE_LAB1_1006',
                                  'IPVE_LAB1_1007', 'IPVE_LAB1_1008', 'IPVE_LAB1_1009',
                                  'IPVE_LAB1_1010'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1004',
        'device_type': 'Polycom_VVX400',
        'device_username': 'IPVE-1004',
        'first_name': 'IPVE Lab',
        'last_name': '1004',
        'extension': '1004',
        'line_port': 'IPVE_LAB1_1004@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1005', 'line_port': 'IPVE_LAB1_1004_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1006', 'line_port': 'IPVE_LAB1_1004_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1001', 'IPVE_LAB1_1002', 'IPVE_LAB1_1003',
                                  'IPVE_LAB1_1007', 'IPVE_LAB1_1008', 'IPVE_LAB1_1009',
                                  'IPVE_LAB1_1010'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1005',
        'device_type': 'Polycom_VVX500',
        'device_username': 'IPVE-1005',
        'first_name': 'IPVE Lab',
        'last_name': '1005',
        'extension': '1005',
        'line_port': 'IPVE_LAB1_1005@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1006', 'line_port': 'IPVE_LAB1_1005_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1007', 'line_port': 'IPVE_LAB1_1005_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1001', 'IPVE_LAB1_1002', 'IPVE_LAB1_1003',
                                  'IPVE_LAB1_1004', 'IPVE_LAB1_1008', 'IPVE_LAB1_1009',
                                  'IPVE_LAB1_1010'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1006',
        'device_type': 'Polycom_VVX600',
        'device_username': 'IPVE-1006',
        'first_name': 'IPVE Lab',
        'last_name': '1006',
        'extension': '1006',
        'line_port': 'IPVE_LAB1_1006@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1007', 'line_port': 'IPVE_LAB1_1006_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1008', 'line_port': 'IPVE_LAB1_1006_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1001', 'IPVE_LAB1_1002', 'IPVE_LAB1_1003',
                                  'IPVE_LAB1_1004', 'IPVE_LAB1_1005', 'IPVE_LAB1_1009',
                                  'IPVE_LAB1_1010'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1007',
        'device_type': 'Polycom_IP335',
        'device_username': 'IPVE-1007',
        'first_name': 'IPVE Lab',
        'last_name': '1007',
        'extension': '1007',
        'line_port': 'IPVE_LAB1_1007@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1008', 'line_port': 'IPVE_LAB1_1007_1@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1001', 'IPVE_LAB1_1002', 'IPVE_LAB1_1003',
                                  'IPVE_LAB1_1004', 'IPVE_LAB1_1005', 'IPVE_LAB1_1006',
                                  'IPVE_LAB1_1009', 'IPVE_LAB1_1010'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1008',
        'device_type': 'Polycom_IP450',
        'device_username': 'IPVE-1008',
        'first_name': 'IPVE Lab',
        'last_name': '1008',
        'extension': '1008',
        'line_port': 'IPVE_LAB1_1008@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1009', 'line_port': 'IPVE_LAB1_1008_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1010', 'line_port': 'IPVE_LAB1_1008_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1001', 'IPVE_LAB1_1002', 'IPVE_LAB1_1003',
                                  'IPVE_LAB1_1004', 'IPVE_LAB1_1005', 'IPVE_LAB1_1006',
                                  'IPVE_LAB1_1007'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1009',
        'device_type': 'Polycom_IP550',
        'device_username': 'IPVE-1009',
        'first_name': 'IPVE Lab',
        'last_name': '1009',
        'extension': '1009',
        'line_port': 'IPVE_LAB1_1009@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1010', 'line_port': 'IPVE_LAB1_1009_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1001', 'line_port': 'IPVE_LAB1_1009_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1002', 'IPVE_LAB1_1003', 'IPVE_LAB1_1004',
                                  'IPVE_LAB1_1005', 'IPVE_LAB1_1006', 'IPVE_LAB1_1007',
                                  'IPVE_LAB1_1008'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1010',
        'device_type': 'Polycom_IP650',
        'device_username': 'IPVE-1010',
        'first_name': 'IPVE Lab',
        'last_name': '1010',
        'extension': '1010',
        'line_port': 'IPVE_LAB1_1010@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB1_1001', 'line_port': 'IPVE_LAB1_1010_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB1_1002', 'line_port': 'IPVE_LAB1_1010_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB1_1003', 'IPVE_LAB1_1004', 'IPVE_LAB1_1005',
                                  'IPVE_LAB1_1006', 'IPVE_LAB1_1007', 'IPVE_LAB1_1008',
                                  'IPVE_LAB1_1009'],
    },
    {
        'group_id': 'IPVE_LAB1',
        'user_id': 'IPVE_LAB1_1011',
        'device_type': 'Polycom-conf',
        'device_username': 'IPVE-1011',
        'first_name': 'IPVE Lab',
        'last_name': '1011',
        'extension': '1011',
        'line_port': 'IPVE_LAB1_1011@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [],
        'busy_lamp_field_users': [],
    },
    # Group 2
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2001',
        #'device_type': 'Polycom_VVX300',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2001',
        'first_name': 'IPVE Lab',
        'last_name': '2001',
        'extension': '2001',
        'line_port': 'IPVE_LAB2_2001@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2002', 'line_port': 'IPVE_LAB2_2001_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2003', 'line_port': 'IPVE_LAB2_2001_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2004', 'IPVE_LAB2_2005', 'IPVE_LAB2_2006',
                                  'IPVE_LAB2_2007', 'IPVE_LAB2_2008', 'IPVE_LAB2_2009',
                                  'IPVE_LAB2_2010'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2002',
        # 'device_type': 'Polycom_VVX300',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2002',
        'first_name': 'IPVE Lab',
        'last_name': '2002',
        'extension': '2002',
        'line_port': 'IPVE_LAB2_2002@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2003', 'line_port': 'IPVE_LAB2_2002_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2004', 'line_port': 'IPVE_LAB2_2002_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2001', 'IPVE_LAB2_2005', 'IPVE_LAB2_2006',
                                  'IPVE_LAB2_2007', 'IPVE_LAB2_2008', 'IPVE_LAB2_2009',
                                  'IPVE_LAB2_2010'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2003',
        # 'device_type': 'Polycom_VVX400',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2003',
        'first_name': 'IPVE Lab',
        'last_name': '2003',
        'extension': '2003',
        'line_port': 'IPVE_LAB2_2003@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2004', 'line_port': 'IPVE_LAB2_2003_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2005', 'line_port': 'IPVE_LAB2_2003_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2001', 'IPVE_LAB2_2002', 'IPVE_LAB2_2006',
                                  'IPVE_LAB2_2007', 'IPVE_LAB2_2008', 'IPVE_LAB2_2009',
                                  'IPVE_LAB2_2010'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2004',
        # 'device_type': 'Polycom_VVX400',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2004',
        'first_name': 'IPVE Lab',
        'last_name': '2004',
        'extension': '2004',
        'line_port': 'IPVE_LAB2_2004@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2005', 'line_port': 'IPVE_LAB2_2004_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2006', 'line_port': 'IPVE_LAB2_2004_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2001', 'IPVE_LAB2_2002', 'IPVE_LAB2_2003',
                                  'IPVE_LAB2_2007', 'IPVE_LAB2_2008', 'IPVE_LAB2_2009',
                                  'IPVE_LAB2_2010'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2005',
        # 'device_type': 'Polycom_VVX500',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2005',
        'first_name': 'IPVE Lab',
        'last_name': '2005',
        'extension': '2005',
        'line_port': 'IPVE_LAB2_2005@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2006', 'line_port': 'IPVE_LAB2_2005_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2007', 'line_port': 'IPVE_LAB2_2005_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2001', 'IPVE_LAB2_2002', 'IPVE_LAB2_2003',
                                  'IPVE_LAB2_2004', 'IPVE_LAB2_2008', 'IPVE_LAB2_2009',
                                  'IPVE_LAB2_2010'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2006',
        # 'device_type': 'Polycom_VVX600',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2006',
        'first_name': 'IPVE Lab',
        'last_name': '2006',
        'extension': '2006',
        'line_port': 'IPVE_LAB2_2006@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2007', 'line_port': 'IPVE_LAB2_2006_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2008', 'line_port': 'IPVE_LAB2_2006_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2001', 'IPVE_LAB2_2002', 'IPVE_LAB2_2003',
                                  'IPVE_LAB2_2004', 'IPVE_LAB2_2005', 'IPVE_LAB2_2009',
                                  'IPVE_LAB2_2010'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2007',
        # 'device_type': 'Polycom_IP335',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2007',
        'first_name': 'IPVE Lab',
        'last_name': '2007',
        'extension': '2007',
        'line_port': 'IPVE_LAB2_2007@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2008', 'line_port': 'IPVE_LAB2_2007_1@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2001', 'IPVE_LAB2_2002', 'IPVE_LAB2_2003',
                                  'IPVE_LAB2_2004', 'IPVE_LAB2_2005', 'IPVE_LAB2_2006',
                                  'IPVE_LAB2_2009', 'IPVE_LAB2_2010'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2008',
        # 'device_type': 'Polycom_IP450',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2008',
        'first_name': 'IPVE Lab',
        'last_name': '2008',
        'extension': '2008',
        'line_port': 'IPVE_LAB2_2008@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2009', 'line_port': 'IPVE_LAB2_2008_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2010', 'line_port': 'IPVE_LAB2_2008_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2001', 'IPVE_LAB2_2002', 'IPVE_LAB2_2003',
                                  'IPVE_LAB2_2004', 'IPVE_LAB2_2005', 'IPVE_LAB2_2006',
                                  'IPVE_LAB2_2007'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2009',
        # 'device_type': 'Polycom_IP550',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2009',
        'first_name': 'IPVE Lab',
        'last_name': '2009',
        'extension': '2009',
        'line_port': 'IPVE_LAB2_2009@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2010', 'line_port': 'IPVE_LAB2_2009_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2001', 'line_port': 'IPVE_LAB2_2009_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2002', 'IPVE_LAB2_2003', 'IPVE_LAB2_2004',
                                  'IPVE_LAB2_2005', 'IPVE_LAB2_2006', 'IPVE_LAB2_2007',
                                  'IPVE_LAB2_2008'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2010',
        # 'device_type': 'Polycom_IP650',
        'device_type': 'Polycom',
        'device_username': 'IPVE-2010',
        'first_name': 'IPVE Lab',
        'last_name': '2010',
        'extension': '2010',
        'line_port': 'IPVE_LAB2_2010@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [
            { 'user_id': 'IPVE_LAB2_2001', 'line_port': 'IPVE_LAB2_2010_1@telapexinc.com' },
            { 'user_id': 'IPVE_LAB2_2002', 'line_port': 'IPVE_LAB2_2010_2@telapexinc.com' }],
        'busy_lamp_field_users': ['IPVE_LAB2_2003', 'IPVE_LAB2_2004', 'IPVE_LAB2_2005',
                                  'IPVE_LAB2_2006', 'IPVE_LAB2_2007', 'IPVE_LAB2_2008',
                                  'IPVE_LAB2_2009'],
    },
    {
        'group_id': 'IPVE_LAB2',
        'user_id': 'IPVE_LAB2_2011',
        'device_type': 'Polycom-conf',
        'device_username': 'IPVE-2011',
        'first_name': 'IPVE Lab',
        'last_name': '2011',
        'extension': '2011',
        'line_port': 'IPVE_LAB2_2011@telapexinc.com',
        'service_pack': 'IPVComplete',
        'appearances': [],
        'busy_lamp_field_users': [],
    },
]


def lab_rebuild(process_id):
    process = Process.objects.get(id=process_id)
    content_key_name = "lab-rebuild_{}.txt".format(datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
    try:
        print("Process {}: {} -> {}".format(process_id, process.method, process.parameters))
        process.status = process.STATUS_RUNNING
        process.save(update_fields=['status'])

        action = process.parameters.get('action', None)

        bwl = BroadWorksLab(process)
        if action == 'Rebuild':
            bwl.rebuild(provider, groups, users)
        elif action == 'Status':
            bwl.status(provider, groups, users)
        process.content[content_key_name] = bwl._content.getvalue()
        process.status = process.STATUS_COMPLETED
        process.end_timestamp = timezone.now()
        process.save(update_fields=['content', 'status', 'end_timestamp'])
    except Exception:
        process.status = process.STATUS_ERROR
        process.content[content_key_name] = bwl._content.getvalue()
        process.end_timestamp = timezone.now()
        process.exception = traceback.format_exc()
        process.save(update_fields=['status', 'content', 'exception', 'end_timestamp'])
