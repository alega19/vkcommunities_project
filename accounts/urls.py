from django.conf.urls import url
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    url('^signup$', views.signup, name='signup'),
    url(
        '^confirm_email_sent$',
        TemplateView.as_view(template_name='accounts/confirm_email_sent.html'),
        name='confirm_email_sent',
    ),
    url('^activate/([0-9A-Za-z_\-]+)/([0-9A-Za-z_\-]+)$', views.activate, name='activate'),
    url('^login$', views.login, name='login'),
    url('^logout$', views.LogoutView.as_view(), name='logout'),
    url('^recover$', views.recover, name='recover'),
    url(
        '^recovery_email_sent$',
        TemplateView.as_view(template_name='accounts/recovery_email_sent.html'),
        name='recovery_email_sent',
    ),
    url('^reset_password/([0-9A-Za-z_\-]+)/([0-9A-Za-z_\-]+)$', views.reset_password, name='reset_password'),
]
