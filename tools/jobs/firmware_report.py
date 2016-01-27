# Python
import io
import re
import datetime
import traceback
from collections import OrderedDict

# Django
from django.utils import timezone

# Application
from tools.models import Process

# Third Party
from lib.pybw.broadworks import BroadWorks, Nil


def firmware_report(process_id):
    process = Process.objects.get(id=process_id)
    try:
        print("Process {}: {} -> {}".format(process_id, process.method, process.parameters))
        process.status = process.STATUS_RUNNING
        process.save(update_fields=['status'])

        content = dict()

        # Retrieve Data
        provider_id = process.parameters.get('provider_id', None)
        group_id = process.parameters.get('group_id', None)

        if provider_id and group_id:
            key_name = "toolchest_firmware_report_{}-{}_{}.csv".format(provider_id, group_id, datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
        elif provider_id:
            key_name = "toolchest_firmware_report_{}_{}.csv".format(provider_id, datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
        else:
            key_name = "toolchest_firmware_report_{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))

        file_content = io.StringIO()

        # Login to BroadWorks
        bw = BroadWorks(url='http://192.168.151.21/webservice/services/ProvisioningService?wsdl',
                        username='develop', password='W4sz2lZHtk^3W)P4+P2VS#IH=H_xXV$3')
        bw.LoginRequest14sp4()

        user_agent_regex = re.compile('^(?P<device_type>PolycomVVX-VVX_\d{3}|PolycomSoundStationIP-SSIP_\d{4}|PolycomSoundPointIP-SPIP_\d{3})-UA\/(?P<version>[\d\.]+)$')
        device_types = ['Polycom', 'Polycom_VVX300', 'Polycom_VVX400', 'Polycom_VVX500', 'Polycom_VVX600']

        file_content.write('"Provider Id","Group Id","Device Type","Device Name","Version","User Agent","Registered"\n')
        content[key_name] = file_content.getvalue()
        process.content = content
        process.save(update_fields=['content'])
        # Process Devices
        for device_type in device_types:
            if provider_id and group_id:
                resp3 = bw.SystemAccessDeviceGetAllRequest(searchCriteriaExactDeviceType={'deviceType': device_type},
                                                           searchCriteriaExactDeviceServiceProvider={'serviceProviderId': provider_id},
                                                           searchCriteriaGroupId=OrderedDict([
                                                                                              ('mode', 'Equal To'),
                                                                                              ('value', group_id),
                                                                                              ('isCaseInsensitive', False),
                                                                                            ]))
            elif provider_id:
                resp3 = bw.SystemAccessDeviceGetAllRequest(searchCriteriaExactDeviceType={'deviceType': device_type},
                                                           searchCriteriaExactDeviceServiceProvider={'serviceProviderId': provider_id})
            else:
                resp3 = bw.SystemAccessDeviceGetAllRequest(searchCriteriaExactDeviceType={'deviceType': device_type})
            devices = resp3['data']['accessDeviceTable']
            for idx, device in enumerate(devices):
                device_provider_id = device['Service Provider Id']
                device_group_id = device['Group Id']
                device_name = device['Device Name']

                if device_provider_id and device_group_id and device_name:
                    resp5 = bw.GroupAccessDeviceGetUserListRequest(device_provider_id, device_group_id, device_name)
                    users = resp5['data']['deviceUserTable']
                elif device_provider_id and device_name:
                    resp5 = bw.ServiceProviderAccessDeviceGetUserListRequest(device_provider_id, device_name)
                    users = resp5['data']['deviceUserTable']
                else:
                    continue
                device_user_agent = None
                device_registered = False
                device_uri = None
                for user in users:
                    user_id = user['User Id']
                    resp6 = bw.UserGetRegistrationListRequest(user_id)
                    registrations = resp6['data']['registrationTable']
                    for reg in registrations:
                        if reg['Device Name'] == device_name:
                            device_user_agent = reg['User Agent']
                            device_registered = True
                            device_uri = reg['URI']
                            break
                    else:
                        continue
                    break
                if device_registered:
                    m = user_agent_regex.match(device_user_agent)
                    if m:
                        reg_device_type = m.group('device_type')
                        reg_version = m.group('version')
                        file_content.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(device_provider_id, device_group_id, device_type, device_name, reg_version, device_user_agent, device_registered))
                        content[key_name] = file_content.getvalue()
                        process.content = content
                        process.save(update_fields=['content'])
                    else:
                        file_content.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(device_provider_id, device_group_id, device_type, device_name, '', device_user_agent, device_registered))
                        content[key_name] = file_content.getvalue()
                        process.content = content
                        process.save(update_fields=['content'])
                else:
                    # Not registered, so blank version/UA
                    file_content.write('"{}","{}","{}","{}","{}","{}","{}"\n'.format(device_provider_id, device_group_id, device_type, device_name, '', '', device_registered))
                    content[key_name] = file_content.getvalue()
                    process.content = content
                    process.save(update_fields=['content'])

        content[key_name] = file_content.getvalue()
        process.content = content
        process.status = process.STATUS_COMPLETED
        process.end_timestamp = timezone.now()
        process.save(update_fields=['content', 'status', 'end_timestamp'])
        file_content.close()
        bw.LogoutRequest()
    except Exception:
        process.status = process.STATUS_ERROR
        process.end_timestamp = timezone.now()
        process.exception = traceback.format_exc()
        process.save(update_fields=['status', 'exception', 'end_timestamp'])
