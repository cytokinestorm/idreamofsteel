from django.conf.urls import patterns, include, url
from plan import views

urlpatterns = patterns('',
    url(r'^$', views.planHome),
    url(r'^user/(?P<username>.+)/(?P<page>\d+)/$', views.planUser),
    url(r'^all/$', views.planAll),
)