from django.core.paginator import Paginator
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template import RequestContext, Context
from traininglog.models import *
from share.models import *
from share.forms import *
from userstats.models import *
from userstats.views import tupProfile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.timezone import utc, get_current_timezone
from django.core.validators import validate_email
import datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from idreamofsteel.constants import *


def getRequestUnit(request):
    if request.user.is_authenticated():
        if request.user.profile.units == UserProfile.METRIC:
            return 'kg'
    return 'lb'


def buildCommentDict(sessionIds):
    commentQuery = SessionComment.objects.filter(session__id__in = sessionIds, status = SessionComment.PUBLISHED).order_by('-create_time').values('session__id', 'id', 'content', 'author__username', 'session__title')[:nRecentComment]
    for iComment in commentQuery:
        iComment['link'] = reverse(blogSession, kwargs = {'sessionid': iComment['session__id']}) + '#c' + str(iComment['id'])
    return commentQuery


def buildSingleSessionDict(iSession):
    # Better way to do this?
    sessionDict = {}
    sessionDict['id'] = iSession.id
    sessionDict['author__username'] = iSession.author.username
    sessionDict['author_id'] = iSession.author.id
    sessionDict['create_time'] = iSession.create_time
    sessionDict['session_date'] = iSession.session_date
    sessionDict['title'] = iSession.title
    sessionDict['content'] = iSession.content
    
    strengthList = Strength.objects.filter(session__id = sessionDict['id']).order_by('id').values('session__id', 'lift_id', 'lift__name', 'sets', 'reps', 'weight', 'mo', 'comments')
    sessionDict['strength_set'] = [x for x in strengthList if x['session__id'] == sessionDict['id']]
    return sessionDict


def buildSessionDict(pagedSession):
    sessionList = pagedSession.object_list.values('id', 'author__username', 'author_id', 'create_time', 'session_date', 'title', 'content')
    sessionIds = [x['id'] for x in sessionList]
    strengthList = Strength.objects.filter(session__id__in = sessionIds).order_by('id').values('session__id', 'lift_id', 'lift__name', 'sets', 'reps', 'weight', 'mo', 'comments')
    commentList = SessionComment.objects.filter(session__id__in = sessionIds).values('session__id')
    for iSession in sessionList:
        iSession['comment_count'] = len([x for x in commentList if x['session__id'] == iSession['id']])
        iSession['strength_set'] = [x for x in strengthList if x['session__id'] == iSession['id']]
    return sessionList


def blogSession(request, sessionid):
    iSession = Session.objects.get(pk = int(sessionid))
    iSessionDict = buildSingleSessionDict(iSession)
    commentForm = SessionCommentForm(prefix = "comment")
    thisAccount, thisProfile, unit = tupProfile(request, iSessionDict['author__username'])
    blogUnit = getRequestUnit(request)
    
    commentList = iSession.sessioncomment_set.order_by('create_time').values('author_id', 'author__username', 'id', 'create_time', 'status', 'content')
    nComment = len(commentList)
    
    if ((request.user.id != iSession.author.id) and (iSession.author.profile.privacy == UserProfile.PRIVATE)) or (iSession.status == Session.DELETED):
        return render_to_response("403.html", context_instance = RequestContext(request))
    else:
        return render_to_response("blog/sessionview.html", 
            {'thisSession': iSession, 'iSessionDict': iSessionDict, 'commentForm': commentForm, 'commentList': commentList, 'nComment': nComment,
             'thisAccount': thisAccount, 'thisProfile': thisProfile, 'unit': unit, 'blogUnit': blogUnit }, 
            context_instance = RequestContext(request))


def blogBuilder(request, allSession, page):
    allPagedSession = Paginator(allSession, nBlogPost)
    pagedSession = allPagedSession.page(int(page))
    pagedSessionDict = buildSessionDict(pagedSession)
    lastpage = allPagedSession.num_pages
    
    recentComments = buildCommentDict(allSession.values_list('id', flat = True))
    blogUnit = getRequestUnit(request)
    
    return (pagedSession, pagedSessionDict, lastpage, recentComments, blogUnit)


def sortColsByRow(inputList, nCol):
    outputList = []
    for i in range((len(inputList) + 1) / nCol):
        outputList.append([])
    
    for i in range(len(inputList)):
        whichRow = i / nCol
        outputList[whichRow].append(inputList[i])
    
    return outputList


def blogAll(request, page = '1'):
    allSession = Session.objects.filter(status = Session.CONFIRMED, author__userprofile__privacy = UserProfile.PUBLIC).order_by('-create_time')
    pagedSession, pagedSessionDict, lastpage, recentComments, blogUnit = blogBuilder(request, allSession, page)
    pagerPath = '/share/blog'
    
    teamList = []
    for iTeam in Team.objects.all().order_by('name'):
        if request.user.is_authenticated() and TeamInvitation.objects.filter(team = iTeam, email = request.user.email).count():
            teamList.append({ 'pretty_name': iTeam.pretty_name, 'name': iTeam.name, 'isInvited': True })
        else:
            teamList.append({ 'pretty_name': iTeam.pretty_name, 'name': iTeam.name, 'isInvited': False })
    teamList = sortColsByRow(teamList, 2)
    
    return render_to_response("blog/blog_all.html", 
        {'pagedSession': pagedSession, 'pagedSessionDict': pagedSessionDict, 'lastpage': lastpage, 'pagerPath': pagerPath, 
         'recentComments': recentComments, 'teamList': teamList, 'blogUnit': blogUnit }, 
        context_instance = RequestContext(request))
            
            
def blogTeam(request, teamname = '', page = '1'):
    thisTeam = get_object_or_404(Team, name = teamname)
    allSession = Session.objects.filter(Q(status = Session.CONFIRMED) & Q(author__team__id = thisTeam.id) & (Q(author__teammembership__type = TeamMembership.MEMBER) | Q(author__teammembership__type = TeamMembership.CAPTAIN))).exclude(author__userprofile__privacy = UserProfile.PRIVATE).order_by('-create_time')
    pagedSession, pagedSessionDict, lastpage, recentComments, blogUnit = blogBuilder(request, allSession, page)
    pagerPath = '/share/blog/team/%s' % teamname
    
    teamRoster = User.objects.filter(Q(teammembership__team = thisTeam), Q(teammembership__type = TeamMembership.CAPTAIN) | Q(teammembership__type = TeamMembership.MEMBER)).order_by('username').values('username', 'teammembership__type')
    teamRoster = sortColsByRow(teamRoster, 2)
    
    # Get status
    status = thisTeam.getStatus(request.user)
    if request.user.is_authenticated():
        if TeamInvitation.objects.filter(team = thisTeam, email = request.user.email).count() != 0:
            status = TeamMembership.INVITED
    
    return render_to_response("blog/blog_team.html", 
            {'pagedSession': pagedSession, 'pagedSessionDict': pagedSessionDict, 'thisTeam': thisTeam, 'lastpage': lastpage, 
             'pagerPath': pagerPath, 'recentComments': recentComments, 'blogUnit': blogUnit, 'teamRoster': teamRoster, 
             'status': status }, 
            context_instance = RequestContext(request))
        

def blogUser(request, username, page = '1'):
    thisUser, thisProfile, unit = tupProfile(request, username)
    if (request.user != thisUser) and (thisUser.profile.privacy == UserProfile.PRIVATE):
        return render_to_response("403.html", context_instance = RequestContext(request))
    else:
        allSession = Session.objects.filter(status = Session.CONFIRMED, author = thisUser).order_by('-create_time')
        pagedSession, pagedSessionDict, lastpage, recentComments, blogUnit = blogBuilder(request, allSession, page)
        pagerPath = '/share/blog/user/%s' % str(username)
        
        liftList = list(set(Strength.objects.filter(session__author__username = username, session__status = Session.CONFIRMED).order_by('lift__name').values_list('lift__name', 'lift__id')))
        liftList.sort()
        
        return render_to_response("blog/blog_user.html",
            {'pagedSession': pagedSession, 'pagedSessionDict': pagedSessionDict, 'lastpage': lastpage, 'thisUser': thisUser, 'pagerPath': pagerPath, 
             'recentComments': recentComments, 'thisAccount': thisUser, 'thisProfile': thisProfile, 'unit': unit, 'blogUnit': blogUnit, 'liftList': liftList},
            context_instance = RequestContext(request))


def blogLift(request, username, liftid, page):
    thisUser, thisProfile, unit = tupProfile(request, username)
    if (request.user != thisUser) and (thisUser.profile.privacy == UserProfile.PRIVATE):
        return render_to_response("403.html", context_instance = RequestContext(request))
    else:
        liftid = int(liftid)
        liftName = ExerciseLookup.objects.get(id = liftid).name
        strengthQuery = Strength.objects.filter(lift_id = liftid, session__author__username = username).values('session_id', 'reps')
        sessionIds = set([session['session_id'] for session in strengthQuery])
        
        allSession = Session.objects.filter(id__in = sessionIds, status = Session.CONFIRMED).order_by('-create_time')
        pagedSession, pagedSessionDict, lastpage, recentComments, blogUnit = blogBuilder(request, allSession, page)
        pagerPath = '/share/blog/lift/%s/lift-%g' % (str(username), liftid)
        
        repRanges = list(set([strength['reps'] for strength in strengthQuery]))
        repRanges.sort()
        repRanges = sortColsByRow(repRanges, 2)
        
        return render_to_response("blog/blog_lift.html",
                {'pagedSession': pagedSession, 'pagedSessionDict': pagedSessionDict, 'lastpage': lastpage, 'thisUser': thisUser, 'pagerPath': pagerPath, 'liftName': liftName,
                 'recentComments': recentComments, 'thisAccount': thisUser, 'thisProfile': thisProfile, 'unit': unit, 'blogUnit': blogUnit, 'repRanges': repRanges, 'liftid': liftid},
                context_instance = RequestContext(request))


def blogReps(request, username, liftid, reps, page):
    thisUser, thisProfile, unit = tupProfile(request, username)
    if (request.user != thisUser) and (thisUser.profile.privacy == UserProfile.PRIVATE):
        return render_to_response("403.html", context_instance = RequestContext(request))
    else:
        liftid = int(liftid)
        liftName = ExerciseLookup.objects.get(id = liftid).name
        reps = int(reps)
        sessionIds = set(Strength.objects.filter(lift_id = liftid, session__author__username = username, reps = reps).values_list('session_id', flat = True))
        
        allSession = Session.objects.filter(id__in = sessionIds, status = Session.CONFIRMED).order_by('-create_time')
        pagedSession, pagedSessionDict, lastpage, recentComments, blogUnit = blogBuilder(request, allSession, page)
        pagerPath = '/share/blog/reps/%s/lift-%g/reps-%g' % (str(username), liftid, reps)
        
        return render_to_response("blog/blog_reps.html",
                {'pagedSession': pagedSession, 'pagedSessionDict': pagedSessionDict, 'lastpage': lastpage, 'thisUser': thisUser, 'pagerPath': pagerPath, 'liftName': liftName,
                 'recentComments': recentComments, 'thisAccount': thisUser, 'thisProfile': thisProfile, 'unit': unit, 'blogUnit': blogUnit, 'reps': reps},
                context_instance = RequestContext(request))


def commentSubmit(request, sessionid):
    commentForm = SessionCommentForm(request.POST, prefix = "comment")
    if commentForm.is_valid() and commentForm.cleaned_data['honeypot'] == '':
        comment = commentForm.save(commit = False)
        comment.session_id = int(sessionid)
        comment.author_id = request.user.id
        comment.create_time = datetime.datetime.now(get_current_timezone())
        comment.status = 1
        comment.save()
        return redirect(comment.link())
    else:
        return redirect("/share/blog/session/%s/#postComment" % sessionid)
        
        
def commentDelete(request, commentid):
    comment = SessionComment.objects.get(pk = int(commentid))
    if request.user.id == comment.author_id:
        comment.status = 2
        comment.save()
        return redirect(comment.link())
    else:
        return render_to_response("403.html", context_instance = RequestContext(request))


def iAmCaptain(user, team):
    if not user.is_authenticated(): # Not even logged in
        return False
    
    if TeamMembership.objects.filter(team = team, user = user).count() == 0: # Not a member of this team
        return False
    
    myClass = TeamMembership.objects.get(team = team, user = user).type
    if myClass == TeamMembership.CAPTAIN:
        return True
    else:
        return False
        
        
@login_required
def teamEdit(request, teamname = ''):
    if teamname == '':
        thisTeamForm = TeamForm()
        type = 'Add'
        oldName = ''
    else:
        thisTeam = get_object_or_404(Team, name = teamname)
        oldName = thisTeam.name
        thisTeamForm = TeamForm(instance = thisTeam)
        type = 'Edit'
        if not iAmCaptain(request.user, thisTeam):
            return render_to_response('403.html', context_instance = RequestContext(request))
    
    return render_to_response('team/teamEdit.html', { 'thisTeamForm': thisTeamForm, 'type': type, 'oldName': oldName }, context_instance = RequestContext(request))


@login_required
def teamSubmit(request):
    teamSubmitType = request.POST['teamSubmit']
    if teamSubmitType == 'Add':
        oldName = ''
        thisTeamForm = TeamForm(request.POST)
    elif teamSubmitType == 'Edit':
        oldName = request.POST['oldName']
        thisTeam = Team.objects.get(name = oldName)
        thisTeamForm = TeamForm(request.POST, instance = thisTeam)
    
    if thisTeamForm.is_valid():
        thisTeam = thisTeamForm.save()
        if teamSubmitType == 'Add':
            newCaptain = TeamMembership(user = request.user, team = thisTeam, type = TeamMembership.CAPTAIN)
            newCaptain.save()
        return redirect('/share/team/view/%s/' % thisTeam.name)
    else:
        return render_to_response('team/teamEdit.html', { 'thisTeamForm': thisTeamForm, 'type': teamSubmitType, 'oldName': oldName }, context_instance = RequestContext(request))
    
    
def teamView(request, teamname):
    thisTeam = get_object_or_404(Team, name = teamname)
    isCaptain = iAmCaptain(request.user, thisTeam)
    
    if isCaptain:
        captainList = User.objects.filter(teammembership__team = thisTeam, teammembership__type = TeamMembership.CAPTAIN).order_by('username')
        memberList = User.objects.filter(teammembership__team = thisTeam, teammembership__type = TeamMembership.MEMBER).order_by('username')
        wannabeList = User.objects.filter(teammembership__team = thisTeam, teammembership__type = TeamMembership.WANNABE).order_by('username')
        invitedList = User.objects.filter(teammembership__team = thisTeam, teammembership__type = TeamMembership.INVITED).order_by('username')
        
        invitedEmailNew = []
        invitedEmail = TeamInvitation.objects.filter(team = thisTeam).order_by('email')
        for iInvited in invitedEmail:
            if User.objects.filter(email = iInvited.email).count() == 0:
                invitedEmailNew.append(iInvited.email)
        
        loserList = User.objects.exclude(team = thisTeam).order_by('username') # exclude invited
        
        isMember = False
        if request.user.is_authenticated():
            if TeamMembership.objects.filter(team = thisTeam, user = request.user).exclude(type = TeamMembership.INVITED).count() > 0:
                isMember = True
        
        return render_to_response('team/teamView.html',
            { 'thisTeam': thisTeam, 'isMember': isMember, 
            'captainList': captainList, 'memberList': memberList, 'wannabeList': wannabeList, 'invitedList': invitedList, 'invitedEmailNew': invitedEmailNew, 'loserList': loserList },
            context_instance = RequestContext(request))
    else:
        return render_to_response("403.html", context_instance = RequestContext(request))
        

@login_required
def teamManage(request, teamname, action, username):
    try: # you must be a member of the team to do any promotions or demotions
        teamid = get_object_or_404(Team, name = teamname).id
        myClass = request.user.teammembership_set.get(team__id = int(teamid)).type
    except:
        return render_to_response('403.html', context_instance = RequestContext(request))
    
    if (myClass != TeamMembership.CAPTAIN and request.user.username == username and action == 'demote') or ( # all except captains can demote self
        myClass == TeamMembership.CAPTAIN and request.user.username != username): # Captains can do anything except affect own status
        
        thisMembership = TeamMembership.objects.get(user__username = username, team__id = int(teamid))
        if action == 'promote':
            if thisMembership.type == TeamMembership.CAPTAIN:
                True # Do nothing
            elif thisMembership.type == TeamMembership.MEMBER:
                thisMembership.type = TeamMembership.CAPTAIN
            elif thisMembership.type == TeamMembership.WANNABE:
                thisMembership.type = TeamMembership.MEMBER
            thisMembership.save()
        elif action == 'demote':
            if thisMembership.type == TeamMembership.CAPTAIN:
                thisMembership.type = TeamMembership.MEMBER
                thisMembership.save()
            elif thisMembership.type == TeamMembership.MEMBER:
                thisMembership.delete()
            elif thisMembership.type == TeamMembership.WANNABE:
                thisMembership.delete()
    
    if myClass == TeamMembership.CAPTAIN:
        return redirect(reverse(teamView, kwargs = {'teamname': teamname}))
    else:
        return redirect(reverse(blogTeam, kwargs = {'teamname': teamname, 'page': 1}))


@login_required
def teamJoin(request, teamname):
    thisTeam = get_object_or_404(Team, name = teamname)
    
    # Find any outstanding invitations
    if TeamMembership.objects.filter(team = thisTeam, user = request.user).count() != 0:
        exMembership = TeamMembership.objects.get(team = thisTeam, user = request.user)
        if exMembership.type == TeamMembership.INVITED:
            exMembership.type = TeamMembership.MEMBER
            exMembership.save()
    if TeamInvitation.objects.filter(team = thisTeam, email = request.user.email).count() != 0:
        exInvitation = TeamInvitation.objects.get(team = thisTeam, email = request.user.email)
        if TeamMembership.objects.filter(team = thisTeam, user = request.user).count() == 0: # No need to duplicate memberships
            newMember = TeamMembership(team = thisTeam, user = request.user, type = TeamMembership.MEMBER)
            newMember.save()
        exInvitation.delete()
    
    # If no invitations, you're just a wannabe
    if TeamMembership.objects.filter(team = thisTeam, user = request.user).count() == 0: # Check if already a member of some sort
        newMember = TeamMembership(team = thisTeam, user = request.user, type = TeamMembership.WANNABE)
        newMember.save()
    
    return redirect(reverse(blogTeam, kwargs = {'teamname': teamname, 'page': 1}))


@login_required
def teamInvite(request, teamname):
    thisTeam = get_object_or_404(Team, name = teamname)
    if not iAmCaptain(request.user, thisTeam):
        return render_to_response('403.html', context_instance = RequestContext(request))
    
    inviteType = request.POST['inviteType']
    if inviteType == 'existing':
        thisUser = get_object_or_404(User, username = request.POST['username'])
        emailList = [thisUser.email]
    elif inviteType == 'new':
        newEmails = request.POST['emailList']
        newEmails = newEmails.replace(' ', '')
        emailList = newEmails.split(',')
    else:
        return render_to_response('404.html', context_instance = RequestContext(request))
    
    for iEmail in emailList:
        inTeam = TeamMembership.objects.filter(team = thisTeam, user__email = iEmail).count()
        alreadyInvited = TeamInvitation.objects.filter(team = thisTeam, email = iEmail).count()
        try:
            validate_email(iEmail)
            if inTeam == 0 and alreadyInvited == 0: # no duplicate invites
                newInvite = TeamInvitation(team = thisTeam, invited_by = request.user, email = iEmail)
                newInvite.save()
                if User.objects.filter(email = iEmail).count() != 0:
                    thisUser = User.objects.get(email = iEmail)
                    newMember = TeamMembership(team = thisTeam, user = thisUser, type = TeamMembership.INVITED)
                    newMember.save()
                
                # Send out invite email
                if False:
                    plaintext = get_template('team/teamInviteEmail.txt')
                    htmly     = get_template('team/teamInviteEmail.html')
                    
                    subject = '[I Dream of Steel] %s Invitation' % teamname
                    from_email = 'admin@idreamofsteel.com'
                    to_email = iEmail
                    
                    msgContext = Context({ 'teamname': teamname, 'inviter': request.user.username })
                    text_content = plaintext.render(msgContext)
                    html_content = htmly.render(msgContext)
                    
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
        except:
            'blahblahblah' # Just do nothing
    return redirect('/share/team/view/%s/' % teamname)
    
    
@login_required
def teamUninvite(request, teamname):
    thisTeam = get_object_or_404(Team, name = teamname)
    if not iAmCaptain(request.user, thisTeam):
        return render_to_response('403.html', context_instance = RequestContext(request))
    
    uninviteType = request.POST['uninviteType']
    if uninviteType == 'existing':
        thisUser = get_object_or_404(User, username = request.POST['username'])
        thisMembership = get_object_or_404(TeamMembership, team = thisTeam, user = thisUser)
        thisMembership.delete()
        try:
            thisInvite = get_object_or_404(TeamInvitation, team = thisTeam, email = thisUser.email)
            thisInvite.delete()
        except:
            'blah blah blah' # Do nothing...invite not found is OK, just leave email invitation outstanding
    elif uninviteType == 'new':
        thisInvite = get_object_or_404(TeamInvitation, team = thisTeam, email = request.POST['email'])
        thisInvite.delete()
    else: 
        return render_to_response('404.html', context_instance = RequestContext(request))
    return redirect('/share/team/view/%s/' % teamname)