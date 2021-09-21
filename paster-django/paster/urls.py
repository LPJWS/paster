from django.conf.urls import url
from django.urls import path
from rest_framework.routers import SimpleRouter

from paster.views import *

router = SimpleRouter()
router.register(r'auth', AuthView, basename='auth')
router.register(r'user', UserView, basename='user')
router.register(r'paste', PasteView, basename='paste')

urlpatterns = [
    # path('auth/send/', reset_password),
    # url(r'^auth/registration/$', TokenViewSet.as_view()),
]

urlpatterns += router.urls
