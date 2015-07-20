from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
from django.contrib import admin
from django.views.generic.simple import direct_to_template
from share.views import blogAll

admin.autodiscover()

urlpatterns = patterns('',
	url(r'^$', blogAll), # replace with a proper homepage
    url(r'^robots\.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),
	
	url(r'^accounts/', include('userstats.urls')),
	url(r'^plot/', include('charts.urls')),
	url(r'^log/', include('traininglog.urls')),
	url(r'^share/', include('share.urls')),
	url(r'^plan/', include('plan.urls')),
    
	url(r'^admin/', include(admin.site.urls)),
)