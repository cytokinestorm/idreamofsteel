from django.conf.urls import patterns, include, url
from charts import views

urlpatterns = patterns('',
    url(r'^leaderboard/(?P<sex>.+)/(?P<lift>.+)/$', views.leaderboard),
    url(r'^tracker/(?P<username>.+)/(?P<liftId>\d+)/$', views.tracker),
    url(r'^tracker-multilift/(?P<username>.+)/(?P<liftId>\d+)/$', views.multiLiftTracker),
    url(r'^tracker-multiuser/(?P<username>.+)/(?P<liftId>\d+)/$', views.multiUserTracker),
)