from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import RequestContext, loader, Context
from traininglog.models import *
from traininglog.forms import *
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory, inlineformset_factory
from django.utils.timezone import utc, get_current_timezone
from django.utils.html import escape
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from idreamofsteel.constants import *
from userstats.models import *
from dateutil.parser import parse
import mimetypes
import datetime
import types
import csv


def logConvertToLbs(input):
    input = input * LBS_PER_KG
    return input


@login_required
def logDefault(request):
    plannedSessions = Session.objects.filter(author = request.user, status = Session.PLANNED, session_date__lte = datetime.date.today()).order_by('session_date')
    if plannedSessions.count():
        oldestPlanId = plannedSessions[0].id
        return redirect(reverse('traininglog.views.updateSession', kwargs = { 'sessionid': oldestPlanId }))
    else:
        year = datetime.datetime.now(get_current_timezone()).strftime('%Y')
        month = datetime.datetime.now(get_current_timezone()).strftime('%m')
        day = datetime.datetime.now(get_current_timezone()).strftime('%d')
        return redirect(reverse('traininglog.views.addSession'))


@login_required
def logMonthly(request, year = '', month = ''):

    def monthIncrement(baseDate, monthInc):
        year = baseDate.year
        month = baseDate.month
        day = baseDate.day
        
        month = month + monthInc
        if month > 12:
            year = year + int(month / 12)
            month = month % 12
        elif month < 1:
            year = year + int((month - 1) / 12)
            month = month - (12 * int((month - 1) / 12))
        
        return datetime.date(year, month, day)
    
    if year == '' or month == '':
        year = datetime.datetime.now(get_current_timezone()).strftime('%Y')
        month = datetime.datetime.now(get_current_timezone()).strftime('%m')
    
    year = int(year)
    month = int(month)

    thisDay = datetime.date(year, month, 1) # Graceful handling of bad entries?
    allSession = Session.objects.filter(session_date__month = month, session_date__year = year, author_id = request.user.id).exclude(status = Session.DELETED).values('title', 'session_date', 'status', 'id')
    
    # Build calendar array
    firstDom = (thisDay.weekday() + 1) % 7 # Shift so Sunday = 0, Saturday = 6
    monthArray = list()
    for iDay in range(firstDom):
        monthArray.append({'weekday': iDay, 'monthday': 0})
    while thisDay.month == month:
        todayContext = {'weekday': (thisDay.weekday() + 1) % 7, 'monthday': thisDay.day, 'addlink': '/log/session/add/%s' % thisDay.strftime('%Y/%m/%d')}
        sessionList = Session.objects.filter(session_date = thisDay, author_id = request.user.id).exclude(status = Session.DELETED).order_by('title')
        sessionList = [session for session in allSession if session['session_date'] == thisDay]
        if len(sessionList) > 0:
            sessionLink = list()
            for thisSession in sessionList:
                sessionLink.append({'title': thisSession['title'], 'status': thisSession['status'], 
                                    'link': reverse('traininglog.views.updateSession', kwargs = {'sessionid': thisSession['id']}), 
                                    'delink': reverse('traininglog.views.deleteSession', kwargs = {'sessionid': thisSession['id']})})
            todayContext['sessionLink'] = sessionLink
        monthArray.append(todayContext)
        thisDay = thisDay + datetime.timedelta(days = 1)
    for iDay in range(thisDay.weekday() + 1, 7):
        monthArray.append({'weekday': iDay, 'monthday': 0})
    
    # Define destinations for navigation links
    thisDay = datetime.date(year, month, 1)
    currentMonth = datetime.date.today().strftime('/log/month/%Y/%m/')
    calNav = {
        'nextMonth': monthIncrement(thisDay, +1).strftime('/log/month/%Y/%m/'),
        'prevMonth': monthIncrement(thisDay, -1).strftime('/log/month/%Y/%m/'),
        'nextYear': datetime.date(year + 1, month, 1).strftime('/log/month/%Y/%m/'),
        'prevYear': datetime.date(year - 1, month, 1).strftime('/log/month/%Y/%m/'),
    }
    
    # Date string
    calTitle = datetime.date(year, month, 1).strftime('%B %Y')
    
    return render_to_response("log/monthlylog.html", {'monthArray': monthArray, 'calNav': calNav, 'calTitle': calTitle, 'currentMonth': currentMonth}, context_instance = RequestContext(request))


def unEscape(input):
    input = input.replace('&amp;', '&')
    input = input.replace('&lt;', '<')
    input = input.replace('&gt;', '>')
    input = input.replace('&quot;', '"')
    input = input.replace('&#39;', "'")
    return(input)


def getLiftList(request):
    liftList = list(ExerciseLookup.objects.filter(Q(user_id = ADMIN) | Q(user_id = request.user.id)).values_list('name', flat = True))
    finalLiftList = [str(x) for x in liftList]
    return finalLiftList


@login_required
def updateSession(request, sessionid):
    sessionid = int(sessionid)
    tempSession = Session.objects.get(pk = sessionid)
    tempSession.content = unEscape(tempSession.content)
    
    thisSession = SessionForm(instance = tempSession, prefix = 'session')
    thisStrengthBuilder = inlineformset_factory(Session, Strength, extra = 1, form = StrengthForm)
    thisStrength = thisStrengthBuilder(instance = tempSession, prefix = 'strength')
    
    # Go through thisStrength and replace liftID with liftName
    for iStrength in thisStrength:
        if iStrength.initial:
            tId = iStrength.save(commit = False).id
            liftName = Strength.objects.get(id = tId).lift.name
            iStrength.initial['lift'] = liftName
    
    thisForm = { 'session': thisSession, 'strength': thisStrength }
    liftList = getLiftList(request)
    
    sessionDate = tempSession.session_date.strftime('%Y-%m-%d')
    currentMonth = tempSession.session_date.strftime('/log/month/%Y/%m/')
    
    if (tempSession.status == Session.PLANNED) and (tempSession.session_date <= datetime.date.today()):
        flipStatus = True
    else:
        flipStatus = False
    
    if (tempSession.author_id != request.user.id) or (tempSession.status == Session.DELETED):
        return render_to_response("403.html", context_instance = RequestContext(request))
    else:
        return render_to_response("log/sessionmodify.html", 
            { 'sessionid': sessionid, 'currentMonth': currentMonth, 'thisForm': thisForm, 'liftList': liftList, 'flipStatus': flipStatus }, 
            context_instance = RequestContext(request))


@login_required
def addSession(request, year = '', month = '', day = ''):
    if year == '' or month == '' or day == '':
        year = datetime.datetime.now(get_current_timezone()).strftime('%Y')
        month = datetime.datetime.now(get_current_timezone()).strftime('%m')
        day = datetime.datetime.now(get_current_timezone()).strftime('%d')
    sessionid = 0
    sessionDate = '%s-%s-%s' % (year, month, day) # Should I check for a valid date here?
    
    thisSession = SessionForm(initial = {'session_date': sessionDate, 'status': 1}, prefix = 'session')
    thisStrengthBuilder = formset_factory(StrengthForm, extra = 1)
    thisStrength = thisStrengthBuilder(prefix = 'strength')
    thisForm = { 'session': thisSession, 'strength': thisStrength }
    liftList = getLiftList(request)
    
    currentMonth = '/log/month/%s/%s' % (year, month)
    return render_to_response("log/sessionmodify.html", 
        {'sessionid': sessionid, 'currentMonth': currentMonth, 'thisForm': thisForm, 'liftList': liftList}, 
        context_instance = RequestContext(request))


@login_required
def deleteSession(request, sessionid):
    sessionid = int(sessionid)
    tSession = Session.objects.get(pk = sessionid)
    
    if tSession.author_id != request.user.id:
        return render_to_response("403.html", context_instance = RequestContext(request))
    else:
        tSession.status = Session.DELETED
        tSession.save()
        tDate = tSession.session_date
        return redirect(reverse('traininglog.views.logMonthly', kwargs = { 'year': tDate.strftime('%Y'), 'month': tDate.strftime('%m') }))


@login_required
def submitSession(request):
    sessionid = int(request.POST['sessionid'])
    if sessionid == 0:
        success = databaseAddSession(request)
    else:
        success = databaseUpdateSession(request)
    
    if type(success) is types.LongType:
        tSession = Session.objects.get(pk = success)
        if tSession.status == Session.CONFIRMED:
            return redirect(reverse('share.views.blogSession', kwargs = { 'sessionid': str(success) }))
        else:
            tDate = tSession.session_date
            return redirect(reverse('traininglog.views.logMonthly', kwargs = { 'year': tDate.strftime('%Y'), 'month': tDate.strftime('%m') }))
    else:
        liftList = getLiftList(request)
        return render_to_response("log/sessionmodify.html", {'sessionid': sessionid, 'currentMonth': request.POST['currentMonth'], 'thisForm': success, 'liftList': liftList}, context_instance = RequestContext(request))

def databaseUpdateSession(request):
    prevSession = Session.objects.get(pk = int(request.POST['sessionid']))
    tSession = SessionForm(request.POST, instance = prevSession, prefix = 'session')
    tStrength = inlineformset_factory(Session, Strength, form = StrengthForm)(request.POST, instance = prevSession, prefix = 'strength')
    
    if tSession.is_valid() and tStrength.is_valid():
        tSession = tSession.save(commit = False)
        tSession.author_id = prevSession.author_id
        tSession.content = escape(tSession.content)
        if (tSession.session_date <= datetime.date.today()) and (tSession.status == Session.PLANNED): # deliberately leave a loophole so the intelligent can publish NOW a log from a long time ago
            tSession.status = Session.CONFIRMED
            tSession.create_time = datetime.datetime.now(get_current_timezone())
        else:
            tSession.status = prevSession.status
            tSession.create_time = prevSession.create_time
        tSession.save()
        if tStrength:
            tStrength.save(commit = False)
            for iStrength in tStrength:
                if iStrength.is_valid():
                    mStrength = iStrength.save(commit = False)
                    if iStrength.cleaned_data:
                        # modify tStrength form so that the lift name is replaced with the lift id
                        # I should eventually fold this into a proper clean_lift method for StrengthForm, but I don't know how to access the user object from the form class
                        liftName = iStrength.cleaned_data['lift']
                        liftCount = ExerciseLookup.objects.filter(Q(name = liftName), Q(user_id = ADMIN) | Q(user_id = request.user.id)).count()
                        if liftCount == 1:
                            mStrength.lift = ExerciseLookup.objects.get(Q(name = liftName), Q(user_id = ADMIN) | Q(user_id = request.user.id))
                        else:
                            mStrength.lift_id = OTHER
                            mStrength.comments = '[['+liftName+']] '+mStrength.comments
                        # And, of course, take care of units
                        if request.user.profile.units == UserProfile.METRIC:
                            mStrength.weight = logConvertToLbs(mStrength.weight)
                        mStrength.save()
    else:
        errorForm = { 'session': tSession, 'strength': tStrength }
        return errorForm
    
    return tSession.id


def databaseAddSession(request):
    tSession = SessionForm(request.POST, prefix = 'session')
    tStrength = formset_factory(StrengthForm)(request.POST, prefix = 'strength')
    
    if tSession.is_valid() and tStrength.is_valid():
        tSession = tSession.save(commit = False)
        tSession.author_id = request.user.id
        tSession.content = escape(tSession.content)
        tSession.create_time = datetime.datetime.now(get_current_timezone())
        if tSession.session_date < datetime.date.today() - datetime.timedelta(days = OLDLOG):
            tSession.status = Session.CONFIRMED
            tSession.create_time = datetime.datetime.combine(tSession.session_date, datetime.time(12, 0, 0, 0, get_current_timezone()))
        elif tSession.session_date <= datetime.date.today():
            tSession.status = Session.CONFIRMED
        else:
            tSession.status = Session.PLANNED
        tSession.save()
        for iStrength in tStrength:
            if iStrength.cleaned_data:
                if request.user.profile.units == UserProfile.METRIC:
                    weightNum = logConvertToLbs(iStrength.cleaned_data['weight'])
                else:
                    weightNum = iStrength.cleaned_data['weight']
                # modify tStrength form so that the lift name is replaced with the lift id
                liftName = iStrength.cleaned_data['lift']
                liftCount = ExerciseLookup.objects.filter(Q(name = liftName), Q(user_id = ADMIN) | Q(user_id = request.user.id)).count()
                if liftCount == 1:
                    liftObj = ExerciseLookup.objects.get(Q(name = liftName), Q(user_id = ADMIN) | Q(user_id = request.user.id))
                else:
                    liftObj = ExerciseLookup.objects.get(id = OTHER)
                    iStrength.cleaned_data['comments'] = '[['+liftName+']] '+iStrength.cleaned_data['comments']
                mStrength = Strength(session_id = tSession.id, 
                                     lift = liftObj, 
                                     sets = iStrength.cleaned_data['sets'], 
                                     reps = iStrength.cleaned_data['reps'], 
                                     weight = weightNum, 
                                     mo = iStrength.cleaned_data['mo'], 
                                     comments = iStrength.cleaned_data['comments'])
                mStrength.save()
    else:
        errorForm = { 'session': tSession, 'strength': tStrength }
        return errorForm
    
    return tSession.id
    
    
@login_required
def exportLog(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename="'+request.user.username+'.log.csv"'
    
    fullLog = Strength.objects.filter(session__author = request.user, session__status = Session.CONFIRMED).order_by('session__session_date').values('session__session_date', 'lift__name', 'sets', 'reps', 'weight', 'comments')
    
    tUnit = request.user.profile.units
    logMatrix = []
    for iEntry in fullLog:
        thisWeight = iEntry['weight']
        if tUnit == UserProfile.METRIC:
            thisWeight = thisWeight / LBS_PER_KG
        logMatrix.append((iEntry['session__session_date'].strftime('%Y-%m-%d'), str(iEntry['lift__name']), int(iEntry['sets']), int(iEntry['reps']), thisWeight, str(iEntry['comments'])))
    
    t = loader.get_template('log/exportToExcel.html')
    c = Context({
        'data': tuple(logMatrix),
    })
    response.write(t.render(c))
    return response
    

IMPORT_TITLE = "Imported Session" #  For imported sessions only. Port to constants if necessary.

@login_required
def importLog(request):
    importForm = logImportForm()
    importedSessions = Session.objects.filter(Q(title = IMPORT_TITLE), Q(status = Session.CONFIRMED) | Q(status = Session.PLANNED), Q(author = request.user))
    return render_to_response("log/importLog.html", {'importForm': importForm, 'importedSessions': importedSessions}, context_instance = RequestContext(request))


@login_required
def importLogSubmit(request):
    # Some quick constants to help process this function only
    DATE = 0
    LIFT = 1
    SETS = 2
    REPS = 3
    WEIGHT = 4
    COMMENTS = 5
    
    importedLog = logImportForm(request.POST, request.FILES)
    if not importedLog.is_valid():
        return importLog(request)
    
    file = request.FILES['logFile']
    fileType = file.content_type
    if fileType not in ('text/csv', 'application/vnd.ms-excel', 'text/plain'): # very crude checker for CSV file format
        return importLog(request)

    try:
        logFull = csv.reader(file)
    except:
        return importLog(request)
    
    allDates = []
    failedRow = []
    cleanedLog = []
    for logRow in logFull:
        try:
            tDate = parse(logRow[DATE]).date()
            tLift = logRow[LIFT]
            tSets = int(logRow[SETS])
            tReps = int(logRow[REPS])
            tWeight = float(logRow[WEIGHT])
            if request.user.profile.units == UserProfile.METRIC:
                tWeight = tWeight * LBS_PER_KG
            if len(logRow) > 5: # magic number! (date + lift + sets + reps + weight is minimum, + comments optional)
                tComments = logRow[COMMENTS]
            else:
                tComments = ''
            cleanedLog.append({'date': tDate, 'lift': tLift, 'sets': tSets, 'reps': tReps, 'weight': tWeight, 'comments': tComments})
            allDates.append(tDate)
        except:
            failedRow.append(logRow)
    
    newSessionList = []
    allDates = list(set(allDates))
    allDates.sort()
    for iDate in allDates:
        if iDate < datetime.date.today() - datetime.timedelta(days = OLDLOG):
            createTime = datetime.datetime.combine(iDate, datetime.time(12, 0, 0, 0, get_current_timezone()))
        else:
            createTime = datetime.datetime.now(get_current_timezone())
        
        if iDate > datetime.date.today():
            sessionStatus = Session.PLANNED
        else:
            sessionStatus = Session.CONFIRMED
        
        newSession = Session(author = request.user, create_time = createTime, session_date = iDate,
                             title = IMPORT_TITLE, status = sessionStatus)
        newSession.save()
        newSessionList.append(newSession)
        
        thisStrength = [iStrength for iStrength in cleanedLog if iStrength['date'] == iDate]
        for iStrength in thisStrength:
            try:
                tLift = ExerciseLookup.objects.get(Q(name = iStrength['lift']), Q(user = request.user) | Q(user_id = ADMIN))
                tComment = iStrength['comments']
            except:
                tLift = ExerciseLookup.objects.get(id = OTHER)
                tComment = '[['+iStrength['lift']+']] '+iStrength['comments']
            newStrength = Strength(session = newSession, lift = tLift, sets = iStrength['sets'],
                                   reps = iStrength['reps'], weight = iStrength['weight'], mo = False, comments = tComment)
            newStrength.save()
    
    return render_to_response("log/importLogPostprocess.html", 
                                {'newSessionList': newSessionList, 'failedLog': failedRow}, 
                                context_instance = RequestContext(request))


@login_required
def liftManager(request):
    myStrengthQuery = Strength.objects.filter(session__author__id = request.user.id, session__status = Session.CONFIRMED).values_list('lift_id', flat = True)
    
    globalLiftQuery = ExerciseLookup.objects.filter(user_id = ADMIN).values('name', 'id')
    globalLiftList = []
    for iLift in globalLiftQuery:
        ct = len([lift for lift in myStrengthQuery if lift == iLift['id']])
        globalLiftList.append({'name': iLift['name'], 'id': iLift['id'], 'ct': ct})
    
    myLiftQuery = ExerciseLookup.objects.filter(user_id = request.user.id)
    myLiftValues = myLiftQuery.values('name', 'id')
    myLiftListBuilder = modelformset_factory(ExerciseLookup, fields = ("name", ), extra = 1, can_delete = True)
    myLiftForm = myLiftListBuilder(queryset = myLiftQuery)
    myLiftList = []
    for iLift in myLiftValues:
        ct = len([lift for lift in myStrengthQuery if lift == iLift['id']])
        myLiftList.append({'name': iLift['name'], 'id': iLift['id'], 'ct': ct})
    
    if not myLiftList: # for new users who don't have any lifts yet
        myLiftList.append({'name': 0, 'id': 0, 'ct': 0})
    myLiftFormAndList = zip(myLiftForm.forms, myLiftList)
    
    return render_to_response("log/liftManager.html", 
                              {'globalLiftList': globalLiftList, 'myLiftForm': myLiftForm, 'myLiftFormAndList': myLiftFormAndList}, 
                              context_instance = RequestContext(request))


@login_required
def liftManagerSubmit(request):
    tLift = modelformset_factory(ExerciseLookup, fields = ("name", ), can_delete = True)(request.POST)
    if tLift.is_valid():
        for iLift in tLift:
            if 'DELETE' in iLift.cleaned_data:
                if iLift.cleaned_data['DELETE']:
                    strengthList = Strength.objects.filter(session__author_id = request.user.id, lift_id = iLift.cleaned_data['id'])
                    for iStrength in strengthList:
                        iStrength.comments = '[['+iStrength.lift.name+']] '+iStrength.comments
                        iStrength.lift_id = OTHER
                        iStrength.save()
        tLift = tLift.save(commit = False)
        if tLift:
            for iLift in tLift:
                existingLift = len(ExerciseLookup.objects.filter(Q(name = iLift.name), Q(user = request.user) | Q(user_id = ADMIN)))
                if not existingLift: # Forbid duplicating existing names
                    iLift.user_id = request.user.id
                    iLift.save()
    else:
        # It shouldn't be possible get here, but still
        return render_to_response("403.html", context_instance = RequestContext(request)) # because I am too lazy to create a proper form error handling ting right now
    
    return redirect(reverse('traininglog.views.liftManager'))