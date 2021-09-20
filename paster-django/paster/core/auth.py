from datetime import datetime

import jwt
from rest_framework import authentication, exceptions

from paster.models import User
from configs import settings


class JWTAuthentication(authentication.TokenAuthentication):
    user_model = User

    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return None
        try:
            access_token = authorization_header.split(' ')[1]
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms='HS256')
        except:
            raise exceptions.AuthenticationFailed({"info": 'Ivalid token'})
        now = datetime.now()
        expire = datetime.strptime(payload['expire'], "%Y-%m-%d %H:%M:%S.%f")
        if now < expire:
            try:
                user = self.user_model.objects.get(id=payload['id'])
            except:
                raise exceptions.NotFound({"info": 'Not found'})
            return user, None
        else:
            raise exceptions.AuthenticationFailed({"info": 'Token expire'})
