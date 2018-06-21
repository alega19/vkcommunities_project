from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.list_, name='list'),
    url(r'^(?P<community_id>[0-9]+)$', views.detail, name='detail'),
    url(r'^posts$', views.post_list, name='post_list'),
]
