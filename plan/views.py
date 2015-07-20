from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext

from idreamofsteel.constants import *
from share.models import *
from share.views import *
from traininglog.models import *
from userstats.models import *
from userstats.views import tupProfile



def planHome(request):
    if request.user.is_authenticated():
        if Session.objects.filter(author = request.user, status = Session.PLANNED).count() > 0:
            return redirect('/plan/user/%s/' % request.user.username)
        else:
            return redirect('/log/month/')
    else:
        return redirect('/log/month/')


def planUser(request, username, page):
    # Get profile (for sidebar)
    thisAccount, thisProfile, unit = tupProfile(request, username)
    
    if thisAccount.profile.privacy == UserProfile.PRIVATE:
        return render_to_response("403.html", context_instance = RequestContext(request))
    
    # Get session list
    allSession = Session.objects.filter(author = thisAccount, status = Session.PLANNED).order_by('session_date')
    pagedSession, pagedSessionDict, lastpage, recentComments, blogUnit = blogBuilder(request, allSession, page)
    pagerPath = '/plan/user/%s' % str(username)
    
    return render_to_response('plan/userPlan.html', 
            {'thisAccount': thisAccount, 'thisProfile': thisProfile, 'blogUnit': blogUnit,
             'pagedSession': pagedSession, 'pagedSessionDict': pagedSessionDict, 'recentComments': recentComments,
             'pagerPath': pagerPath, 'lastpage': lastpage}, 
            context_instance = RequestContext(request))


def planAll(request):
    return render_to_response('plan/allPlan.html', context_instance = RequestContext(request))