# Python
import requests
from io import BytesIO

# Application
from platforms.models import BroadworksPlatform 

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

        response = requests.get(
            'http://10.200.5.20/servlet/LocateUser',
            params=toolParams
        )

        tree = etree.parse(BytesIO(bytes(response.text, 'utf-8')))
        servers = tree.find('applicationServerArray')
        if servers is not None:
            for ele in servers:
                addr = ele.get('address')
                platform = BroadworksPlatform.objects.filter(ip__contains=addr)
                print(platform.Name)

            return etree.tostring(tree, pretty_print=True) 
        else:
            return 'Not Found'
