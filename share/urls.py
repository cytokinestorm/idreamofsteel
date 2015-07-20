from django.conf.urls import patterns, include, url
from share import views, feeds

urlpatterns = patterns('',
    url(r'^blog/(?P<page>\d+)/$', views.blogAll),
    url(r'^blog/team/(?P<teamname>.+)/(?P<page>\d+)/$', views.blogTeam),
    url(r'^blog/user/(?P<username>.+)/(?P<page>\d+)/$', views.blogUser),
    url(r'^blog/lift/(?P<username>.+)/lift-(?P<liftid>\d+)/(?P<page>\d+)/$', views.blogLift),
    url(r'^blog/reps/(?P<username>.+)/lift-(?P<liftid>\d+)/reps-(?P<reps>\d+)/(?P<page>\d+)/$', views.blogReps),
    url(r'^blog/session/(?P<sessionid>\d+)/$', views.blogSession),
    url(r'^blog/comment/submit/(?P<sessionid>\d+)/$', views.commentSubmit),
    url(r'^blog/comment/delete/(?P<commentid>\d+)/$', views.commentDelete),
    
    url(r'^team/add/$', views.teamEdit),
    url(r'^team/edit/(?P<teamname>.+)/$', views.teamEdit),
    url(r'^team/invite/(?P<teamname>.+)/$', views.teamInvite),
    url(r'^team/join/(?P<teamname>.+)/$', views.teamJoin),
    url(r'^team/manage/(?P<teamname>.+)/(?P<action>.+)/(?P<username>.+)/$', views.teamManage),
    url(r'^team/submit/$', views.teamSubmit),
    url(r'^team/uninvite/(?P<teamname>.+)/$', views.teamUninvite),
    url(r'^team/view/(?P<teamname>.+)/$', views.teamView),
    
    url(r'^feed/rss/all/$', feeds.RssAllFeed()),
    url(r'^feed/rss/team/(?P<team>.+)/$', feeds.RssTeamFeed()),
    url(r'^feed/rss/user/(?P<username>.+)/$', feeds.RssUserFeed()),
)