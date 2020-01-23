# Python
import requests
from io import BytesIO

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
        

        response = requests.get(
            'http://10.200.5.20/servlet/LocateUser',
            params={'url': url, 'callPRequest': 'false'}
        )

        #return response.text
        tree = etree.parse(BytesIO(bytes(response.text, 'utf-8')))
        servers = tree.find('applicationServerArray')
        for ele in servers:
            print(ele.get('address'))
        return etree.tostring(tree, pretty_print=True) 
