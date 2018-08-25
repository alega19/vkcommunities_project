from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r'^$',
        views.CommunityListView.as_view(),
        name='community_list',
    ),
    url(
        r'^(?P<pk>[0-9]+)$',
        views.CommunityDetailView.as_view(),
        name='community_detail',
    ),
    url(
        r'^posts$',
        views.PostListView.as_view(),
        name='post_list',
    ),
]
