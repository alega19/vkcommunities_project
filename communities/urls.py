from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.list_, name='list'),
    url(r'^(?P<community_id>[0-9]+)$', views.detail, name='detail'),
]
