from base64 import b64encode

from django.middleware.csrf import get_token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class RootAPIView(APIView):

    def get(self, request, format=None):
        context = {
            'routing': reverse('api:routing-root', request=request, format=format),
            'tools': reverse('api:tools-root', request=request, format=format),
        }
        return Response(context)


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        credentials = f"{request.data['username']}:{request.data['password']}"
        encodedCredentials = str(b64encode(credentials.encode("utf-8")), "utf-8")
        return Response({
            'token': encodedCredentials,
        })

