from django.conf.urls import url

from . import views


urlpatterns = [
    url('^signup$', views.signup, name='signup'),
    url('^confirm_email_sent$', views.confirm_email_sent, name='confirm_email_sent'),
    url('^activate/([0-9A-Za-z_\-]+)/([0-9A-Za-z_\-]+)$', views.activate, name='activate'),
    url('^login$', views.login, name='login'),
    url('^logout$', views.logout, name='logout'),
    url('^recover$', views.recover, name='recover'),
    url('^recovery_email_sent$', views.recovery_email_sent, name='recovery_email_sent'),
    url('^reset_password/([0-9A-Za-z_\-]+)/([0-9A-Za-z_\-]+)$', views.reset_password, name='reset_password'),
]
