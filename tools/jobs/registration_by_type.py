# Python
import io
import datetime
import traceback

# Django
from django.utils import timezone
from django.conf import settings

# Application
from tools.models import Process

# Third Party
from lib.pyutil.util import Util
from lib.pybw.broadworks import BroadWorks, Nil


def registration_by_type(process_id):
    process = Process.objects.get(id=process_id)
    try:
        print("Process {}: {} -> {}".format(process_id, process.method, process.parameters))
        process.status = process.STATUS_RUNNING
        process.save(update_fields=['status'])

        content = dict()
        detail_file_key = "device_report_details_{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
        summary_file_key = "device_report_summary_{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S"))
        detail_file = io.StringIO()
        summary_file = io.StringIO()
        detail_file.write('"{}","{}","{}","{}","{}","{}"\n'.format("Provider Id", "Group Id", "Device Name", "Device Type", "Device User Agent", "Registered"))
        summary_file.write('"{}","{}","{}","{}"\n'.format('Device Type', 'Device Count', 'Registration Count', 'Perc Registered'))

        bw = BroadWorks(**settings.PLATFORMS['broadworks'])
        bw.LoginRequest14sp4()
        device_types = ['Polycom Soundpoint IP 300', 'Polycom Soundpoint IP 320 330',
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

        device_count = dict()
        registration_count = dict()
        for device_type in device_types:
            device_count[device_type] = 0
            registration_count[device_type] = 0

            # Process Devices
            resp3 = bw.SystemAccessDeviceGetAllRequest(searchCriteriaExactDeviceType={'deviceType': device_type})
            devices = resp3['data']['accessDeviceTable']
            if len(devices):
                for idx, device in enumerate(devices):
                    device_count[device_type] += 1
                    provider_id = device['Service Provider Id']
                    group_id = device['Group Id']
                    device_name = device['Device Name']

                    if provider_id and group_id and device_name:
                        resp5 = bw.GroupAccessDeviceGetUserListRequest(provider_id, group_id, device_name)
                        users = resp5['data']['deviceUserTable']
                    elif provider_id and device_name:
                        resp5 = bw.ServiceProviderAccessDeviceGetUserListRequest(provider_id, device_name)
                        users = resp5['data']['deviceUserTable']
                    else:
                        continue
                    device_registered = False
                    device_user_agent = None
                    for user in users:
                        user_id = user['User Id']
                        resp6 = bw.UserGetRegistrationListRequest(user_id)
                        registrations = resp6['data']['registrationTable']
                        for reg in registrations:
                            if reg['Device Name'] == device_name:
                                device_registered = True
                                device_user_agent = reg['User Agent']
                                break
                        else:
                            continue
                        break
                    detail_file.write('"{}","{}","{}","{}","{}","{}"\n'.format(provider_id, group_id, device_name, device_type, device_user_agent, device_registered))
                    if device_registered:
                        registration_count[device_type] += 1

            # Save process end of each type
            if device_count[device_type] > 0:
                perc_registered = (registration_count[device_type] / device_count[device_type]) * 100
            else:
                perc_registered = 0
            summary_file.write('"{}","{}","{}","{:0.2f}%"\n'.format(device_type, device_count[device_type], registration_count[device_type], perc_registered))
            content[detail_file_key] = detail_file.getvalue()
            content[summary_file_key] = summary_file.getvalue()
            process.content = content
            process.save(update_fields=['content'])

        total_device_count = 0
        total_registration_count = 0
        for device_type in device_types:
            total_device_count += device_count[device_type]
            total_registration_count += registration_count[device_type]
        if total_device_count > 0:
            total_perc_registered = (total_registration_count / total_device_count) * 100
        else:
            total_perc_registered = 0
        summary_file.write('"{}","{}","{}","{:0.2f}%"\n'.format('TOTAL', total_device_count, total_registration_count, total_perc_registered))

        content[detail_file_key] = detail_file.getvalue()
        content[summary_file_key] = summary_file.getvalue()
        process.content = content
        process.status = process.STATUS_COMPLETED
        process.end_timestamp = timezone.now()
        process.save(update_fields=['content', 'status', 'end_timestamp'])
        detail_file.close()
        summary_file.close()
        bw.LogoutRequest()
    except Exception:
        process.status = process.STATUS_ERROR
        process.end_timestamp = timezone.now()
        process.exception = traceback.format_exc()
        process.save(update_fields=['status', 'exception', 'end_timestamp'])
