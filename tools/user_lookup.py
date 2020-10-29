# Python
import requests
from io import BytesIO

# Application
from platforms.models import BroadworksPlatform 
from django.conf import settings
from django.db.models import Q

# Third party
from lxml import etree

class UserLocationLookup():
    def __init__(self, parameters):
        self.parameters = parameters

    def run(self):

        # parameters
        url = self.parameters.get('url', '')
        line_port = self.parameters.get('line_port', '')
        dn = self.parameters.get('dn', '')
        group_id = self.parameters.get('group_id', '')

        if url == '' and line_port == '' and dn == '':
            raise Exception("You must enter either a URL, LinePort, or DN")
        
        toolParams = {'callPRequest': 'false'}
        if url != '':
            toolParams['url'] = url
        if line_port != '':
            toolParams['linePort'] = line_port
        if dn:
            toolParams['dn'] = dn
        if group_id != '':
            toolParams['groupId'] = group_id

        lookup_ns = settings.PLATFORMS['locate_user_ns']
        response = requests.get(
            lookup_ns['url'],
            params=toolParams
        )

        tree = etree.parse(BytesIO(bytes(response.text, 'utf-8')))
        bws = []
        servers = tree.find('applicationServerArray')
        if servers is not None:
            for ele in servers:
                addr = ele.get('address')
                platform = BroadworksPlatform.objects.filter(Q(ip__contains=addr)|Q(hostname__contains=addr)).values()
                if len(platform) > 0:
                    bws.append(platform[0])

        return bws
