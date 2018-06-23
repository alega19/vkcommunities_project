from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.community_list, name='community_list'),
    url(r'^(?P<community_id>[0-9]+)$', views.community_detail, name='community_detail'),
    url(r'^posts$', views.post_list, name='post_list'),
]
