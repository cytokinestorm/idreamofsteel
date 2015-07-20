from django.conf.urls import patterns, include, url
from traininglog import views

urlpatterns = patterns('',
	url(r'^$', views.logDefault),
	
    url(r'^month/$', views.logMonthly), # Remove this and code better
	url(r'^month/(?P<year>\d{4})/(?P<month>\d{2})/$', views.logMonthly),
	
    url(r'^session/(?P<sessionid>\d+)/$', views.updateSession),
	url(r'^session/add/$', views.addSession), # Remove this and code better
	url(r'^session/add/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$', views.addSession),
	url(r'^session/delete/(?P<sessionid>\d+)/$', views.deleteSession),
	url(r'^session/submit/$', views.submitSession),
	
    url(r'^export/$', views.exportLog),
	url(r'^import/$', views.importLog),
    url(r'^import/submit/$', views.importLogSubmit),
    
    url(r'^liftManager/$', views.liftManager),
    url(r'^liftManager/submit/$', views.liftManagerSubmit),
)