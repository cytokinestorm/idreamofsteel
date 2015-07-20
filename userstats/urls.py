from django.conf.urls import patterns, include, url
from django.contrib.auth.views import *
from userstats import views

urlpatterns = patterns('',
	url(r'^login/$', views.idosLogin),
	url(r'^logout/$', logout),
    url(r'^profile/$', views.editProfile),
	url(r'^profile/view/(?P<username>.+)/$', views.viewProfile),
    url(r'^profile/edit/$', views.editProfile),
	url(r'^profile/submit/$', views.submitProfile),
	url(r'^create/$', views.createUser),
	
	url(r'^password/change/$', password_change, { 'post_change_redirect': '/accounts/profile/edit/?passChange=1' }),
	
	url(r'^login/reset/$', password_reset, { 'post_reset_redirect': '/accounts/login/?resetMessage=1' }),
	url(r'^login/reset/confirm/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)/$', password_reset_confirm, { 'post_reset_redirect': '/accounts/login/?resetSuccess=1' }),
)