# Python
import requests

class UserLocationLookup():
    def __init__(self, parameters):
        self.parameters = parameters

    def run(self):

        # parameters
        url = self.parameters['url']
        #line_port = self.parameters.get('line_port', None)
        #dn = self.parameters.get('dn', None)
        #group_id = self.parameters.get('group_id', None)

        response = requests.get(
            'http://10.200.5.20/servlet/LocateUser',
            params={'url': '2056082081@tekvoice.net', 'callPRequest': 'false'}
        )

        return response.text

