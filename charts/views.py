from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import *
from django.core.urlresolvers import reverse
from idreamofsteel.constants import *
from idreamofsteel.util import *
from userstats.models import *
import userstats
import share
from traininglog.models import *
from math import *


def getClassData(classId, weightRange, liftMat, unitIdx):
    classData = []
    for iWeight in weightRange:
        classData.append([iWeight, round(getClassLiftWeight(iWeight, classId, liftMat, unitIdx), 1)])
    return classData


def leaderboard(request, sex, lift):
    unitIdx = UserProfile.IMPERIAL
    units = 'lb'
    if request.user.is_authenticated():
        if request.user.profile.units == UserProfile.METRIC:
            unitIdx = UserProfile.METRIC
            units = 'kg'
    
    if sex == 'men':
        sex = 'Men'
        sexId = UserProfile.MALE
    elif sex == 'women':
        sex = 'Women'
        sexId = UserProfile.FEMALE
    
    if lift == 'total':
        plotType = 'Total'
        liftMat = TOTAL_CLASS[sexId]
        meetStr = 'total_meet'
        gymStr = 'total_gym'
    elif lift == 'squat':
        plotType = 'Squat'
        liftMat = SQUAT_CLASS[sexId]
        meetStr = 'squat_meet'
        gymStr = 'squat_gym'
    elif lift == 'bench':
        plotType = 'Bench Press'
        liftMat = BENCH_CLASS[sexId]
        meetStr = 'bench_meet'
        gymStr = 'bench_gym'
    elif lift == 'deadlift':
        plotType = 'Deadlift'
        liftMat = DEADLIFT_CLASS[sexId]
        meetStr = 'dead_meet'
        gymStr = 'dead_gym'
    
    lifterSet = UserProfile.objects.filter(sex = sexId).values('pl_weightclass', 'weight', meetStr, gymStr, 'privacy', 'user__username')
    
    meetData = []
    for iLifter in lifterSet:
        if iLifter['pl_weightclass'] is None:
            continue
        
        meet_weight = dict(PL_WEIGHTCLASSWT)[iLifter['pl_weightclass']]
        if iLifter['weight'] is None:
            thisX = meet_weight
        else:
            thisX = min(meet_weight, iLifter['weight'])
        
        if iLifter[meetStr] is None:
            continue
        thisY = iLifter[meetStr]
        
        if unitIdx == UserProfile.METRIC:
            thisX = thisX / LBS_PER_KG
            thisY = thisY / LBS_PER_KG
        
        thisX = round(thisX, 1)
        thisY = round(thisY, 1)
        if iLifter['privacy'] == UserProfile.PRIVATE:
            meetData.append({ 'name': str('Private User'), 'x': thisX, 'y': thisY })
        else:
            thisLink = reverse(userstats.views.viewProfile, kwargs = {'username': iLifter['user__username']})
            meetData.append({ 'name': str(iLifter['user__username']), 'x': thisX, 'y': thisY, 'link': thisLink })
        
    gymData = []
    for iLifter in lifterSet:
        if iLifter['weight'] is None:
            continue
        
        thisX = iLifter['weight']
        
        if iLifter[gymStr] is None:
            continue
        thisY = iLifter[gymStr]
        
        if unitIdx == UserProfile.METRIC:
            thisX = thisX / LBS_PER_KG
            thisY = thisY / LBS_PER_KG
        
        thisX = round(thisX, 1)
        thisY = round(thisY, 1)
        if iLifter['privacy'] == UserProfile.PRIVATE:
            gymData.append({ 'name': str('Private User'), 'x': thisX, 'y': thisY })
        else:
            thisLink = reverse(userstats.views.viewProfile, kwargs = {'username': iLifter['user__username']})
            gymData.append({ 'name': str(iLifter['user__username']), 'x': thisX, 'y': thisY, 'link': thisLink })
    
    # Determine chart range
    xPrec = 5
    yPrec = 10
    r = 0.05
    
    minX = min([member['x'] for member in gymData] + [member['x'] for member in meetData])
    maxX = max([member['x'] for member in gymData] + [member['x'] for member in meetData])
    minY = min([member['y'] for member in gymData] + [member['y'] for member in meetData])
    maxY = max([member['y'] for member in gymData] + [member['y'] for member in meetData])
    
    xBand = maxX * r
    yBand = maxY * r
    
    minX = floor((minX - xBand) / xPrec) * xPrec
    maxX = ceil((maxX + xBand) / xPrec) * xPrec
    minY = floor((minY - yBand) / yPrec) * yPrec
    maxY = ceil((maxY + yBand) / yPrec) * yPrec
    
    weightRange = range(int(minX), int(maxX) + 1)
    elite = getClassData(ELITE, weightRange, liftMat, unitIdx)
    advanced = getClassData(ADVANCED, weightRange, liftMat, unitIdx)
    intermediate = getClassData(INTERMEDIATE, weightRange, liftMat, unitIdx)
    novice = getClassData(NOVICE, weightRange, liftMat, unitIdx)
    untrained = getClassData(UNTRAINED, weightRange, liftMat, unitIdx)
    
    return render_to_response('plot/leaderboard.html', { 
            'units': units, 'plotType': plotType, 'sex': sex,
            'elite': elite, 'advanced': advanced, 'intermediate': intermediate, 
            'novice': novice, 'untrained': untrained,
            'meetData': meetData, 'gymData': gymData,
            'minX': minX, 'maxX': maxX, 'minY': minY, 'maxY': maxY
        }, context_instance = RequestContext(request))
        
        
def getMyLifts(userid, liftId):
    myLiftListQuery = list(set(Strength.objects.filter(reps__gt = 0, sets__gt = 0, session__author__id = userid, session__status = Session.CONFIRMED).values_list('lift__name', 'lift')))
    myLiftListQuery.sort()
    myLiftList = []
    for iLift in myLiftListQuery:
        if iLift[1] != OTHER: # Don't append "Other" because it makes no sense to track it
            if iLift[1] == liftId:
                myLiftList.append({ 'name': iLift[0], 'id': iLift[1], 'active': True })
            else:
                myLiftList.append({ 'name': iLift[0], 'id': iLift[1], 'active': False })
    return myLiftList


def getTrackerUser(request, username):
    thisUser = get_object_or_404(User, username = username)
    if (request.user.id != thisUser.id) and (thisUser.profile.privacy == UserProfile.PRIVATE):
        return (False, False)
    else:
        userid = thisUser.id
        username = thisUser.username
    unitIdx = UserProfile.IMPERIAL
    if request.user.is_authenticated():
        unitIdx = request.user.profile.units
    return (userid, unitIdx)


def tracker(request, username, liftId):
    userid, unitIdx = getTrackerUser(request = request, username = username)
    if userid == False:
        return render_to_response("403.html", context_instance = RequestContext(request))
    liftId = int(liftId)
    liftName = get_object_or_404(ExerciseLookup, id = liftId).name # variable no longer used, but useful for returning 404 instead of just an empty chart
    myLiftList = getMyLifts(userid = userid, liftId = liftId)
    
    workSetData, estMaxData = getEstMaxTimeseries(userId = userid, liftId = liftId, unitId = unitIdx)
    
    return render_to_response('plot/tracker.html', { 
            'username': username, 'liftId': liftId, 'liftList': myLiftList,
            'estMaxData': estMaxData, 'workSetData': workSetData
        }, context_instance = RequestContext(request))


def multiLiftTracker(request, username, liftId):
    userid, unitIdx = getTrackerUser(request = request, username = username)
    if userid == False:
        return render_to_response("403.html", context_instance = RequestContext(request))
    liftId = int(liftId)
    liftName = get_object_or_404(ExerciseLookup, id = liftId).name # variable no longer used, but useful for returning 404 instead of just an empty chart
    myLiftList = getMyLifts(userid = userid, liftId = 1)
    
    liftMaxes = []
    baseIdx = 0
    baseSeries = 0
    for iLift in myLiftList:
        workSetData, estMaxData = getEstMaxTimeseries(userId = userid, liftId = iLift['id'], unitId = unitIdx)
        if iLift['id'] == liftId:
            liftMaxes.append({'name': iLift['name'], 'data': estMaxData, 'isme': True})
            baseSeries += baseIdx # implemented thusly to account for users with no lifts
        else:
            liftMaxes.append({'name': iLift['name'], 'data': estMaxData, 'isme': False})
        baseIdx += 1
    
    return render_to_response('plot/trackerMultiLift.html', {
            'username': username, 'liftId': liftId, 'liftMaxes': liftMaxes, 'baseSeries': baseSeries
    }, context_instance = RequestContext(request))


def multiUserTracker(request, username, liftId):
    userid, unitIdx = getTrackerUser(request = request, username = username)
    if userid == False:
        return render_to_response("403.html", context_instance = RequestContext(request))
    liftId = int(liftId)
    liftName = get_object_or_404(ExerciseLookup, id = liftId).name # variable no longer used, but useful for returning 404 instead of just an empty chart
    
    # Create a list of benchmark lifts. Only include admin lifts for now. In the future, add ability to include team benchmarks.
    globalLiftList = ExerciseLookup.objects.filter(user_id = ADMIN).exclude(id = OTHER) # include all admin lifts except for 'Other'
    myLiftList = []
    for iLift in globalLiftList:
        if iLift.id == liftId:
            myLiftList.append({ 'name': iLift.name, 'id': iLift.id, 'active': True })
        else:
            myLiftList.append({ 'name': iLift.name, 'id': iLift.id, 'active': False })
    
    userList = list(set(Strength.objects.filter(lift = liftId, session__status = Session.CONFIRMED).exclude(session__author__userprofile__privacy = UserProfile.PRIVATE).values_list('session__author__username', 'session__author__id')))
    userList.sort()
    
    liftMaxes = []
    baseIdx = 0
    baseSeries = 0
    for iUser in userList:
        workSetData, estMaxData = getEstMaxTimeseries(userId = iUser[1], liftId = liftId, unitId = unitIdx)
        if iUser[1] == userid:
            liftMaxes.append({'name': iUser[0], 'data': estMaxData, 'isme': True})
            baseSeries += baseIdx # implemented thusly to account for users with no lifts
        else:
            liftMaxes.append({'name': iUser[0], 'data': estMaxData, 'isme': False})
        baseIdx += 1
    
    return render_to_response('plot/trackerMultiUser.html', {
            'username': username, 'liftId': liftId, 'liftMaxes': liftMaxes, 'liftList': myLiftList, 'baseSeries': baseSeries
    }, context_instance = RequestContext(request))