from django.core.urlresolvers import reverse
from userstats.models import *
from idreamofsteel.constants import *
from traininglog.models import *
import datetime
import share
import time

def Z(x):
    # Pretties up field query for printing
    sigFig = 1
    if x is None:
        return 0
    return round(x, sigFig)


def getClassLiftWeight(userWeight, classIndex, classRef, units = UserProfile.IMPERIAL):
    # Returns the weight corresponding to a CLASSINDEX-class lift at USERWEIGHT using CLASSREF to specify the lift
    # userWeight is the user's weight
    # classIndex is the index of Elite, Advanced, etc. that you want to get the value for
    # classRef is the gender-specific tuple of tuples storing the pre-stored classifications for this lift
    # see idreamofsteel.constants for more information
    loBd = () # tuple for the lower bound of your weight
    upBd = () # for the upper bound
    if units == UserProfile.METRIC:
        userWeight = float(userWeight) * LBS_PER_KG
    for iClass in classRef:
        tWeight = iClass[WEIGHTCLASS]
        if tWeight <= userWeight:
            loBd = iClass
        if tWeight >= userWeight:
            upBd = iClass
            break
    
    if not loBd and upBd: # Below featherweight
        wMult = float(upBd[ATTEMPT][classIndex]) / float(upBd[WEIGHTCLASS])
        attempt = wMult * float(userWeight)
    
    if loBd and not upBd: # Above superheavy
        attempt = loBd[ATTEMPT][classIndex]
    
    if loBd == upBd: # On a band
        attempt = loBd[ATTEMPT][classIndex]
    
    if loBd != upBd and loBd and upBd: # Between bands
        upMult = float(upBd[ATTEMPT][classIndex]) / float(upBd[WEIGHTCLASS])
        loMult = float(loBd[ATTEMPT][classIndex]) / float(loBd[WEIGHTCLASS])
        upTilt = (float(userWeight) - float(loBd[WEIGHTCLASS])) / (float(upBd[WEIGHTCLASS]) - float(loBd[WEIGHTCLASS]))
        loTilt = 1 - upTilt
        wMult = loMult * loTilt + upMult * upTilt
        attempt = wMult * float(userWeight)
    
    if units == UserProfile.METRIC:
        attempt = float(attempt) / LBS_PER_KG
    
    return attempt


def fixUnit(weight, unitId):
    if unitId == UserProfile.METRIC:
        weight = weight / LBS_PER_KG
        unitLabel = 'kg'
    else:
        unitLabel = 'lb'
    return (weight, unitLabel)

def getEstMaxTimeseries(userId, liftId, unitId):
    liftQuery = Strength.objects.filter(reps__gt = 0, sets__gt = 0, lift = liftId, session__author__id = userId, session__status = Session.CONFIRMED).order_by('session__session_date').values('session__session_date', 'session_id', 'weight', 'reps', 'sets')
    liftDates = [x['session__session_date'] for x in liftQuery]
    liftDates = list(set(liftDates))
    liftDates.sort()
    
    estMaxData = []
    workSetData = []
    prevDate = None
    prevMax = None
    # Iterate through all dates to calculate a predicted max.
    for iDate in liftDates:
        unixDate = time.mktime(iDate.timetuple()) * 1000 # x-values
        todayLift = [x for x in liftQuery if x['session__session_date'] == iDate]
        
        # Calculate today's max. Consider a session where you lift SxRxW of 3x5x405 and 2x2x455
        tLiftMax = -float('Inf') # The heaviest weight actually lifted today (455)
        tMaxWeight = -float('Inf') # The heaviest predicted max from a single SxRxW entry (405/.82 = 494)
        for tLift in todayLift:
            tReps = min(tLift['reps'], len(REPMAX))
            tSets = min(tLift['sets'], len(REPMAX[tReps]))
            xMax = round(tLift['weight'] / REPMAX[tReps][tSets], 0) # FW BUG?: This seems to not get the right row/column entry in the REPMAX table
            if xMax > tMaxWeight:
                tMaxWeight = xMax
                iLift = tLift
            if tLift['weight'] > tLiftMax:
                tLiftMax = tLift['weight']
        
        tLiftMax, unitLabel = fixUnit(tLiftMax, unitId)
        iLiftWeight, unitLabel = fixUnit(iLift['weight'], unitId) # The weight of the SxRxW entry that was used to calculate your max (405)
        tMaxWeight, unitLabel = fixUnit(tMaxWeight, unitId)
        
        if prevMax == None and prevDate == None: # Clearly, if this is your first entry, your max is just your max
            iMaxWeight = tMaxWeight
        else:
            nDays = (iDate - prevDate).days # Days since the last time a max was calculated for this lift
            upHl = 7 # Half life of weight multiplier if your currently predicted max is ABOVE your previously predicted max. See ~/helpers/max.decay.xlsx for details
            downHl = 21 # Half life of weight multiplier if your currently predicted max is BELOW your previously predicted max
            prevWeight = 0.5 ** (nDays / upHl) # Weight to assign to your previous max
            if tMaxWeight < prevMax: # previous PRs are "sticky," though they can fall given enough time
                curWeight = 1.25 ** (nDays - downHl) # Weight to use for your current max. Note that if your current max is below your previous max, and your previous max is recent, the more recent number is *penalized* (nDays - downHl is negative)
            else:
                curWeight = 1
            iMaxWeight = max(tLiftMax, tMaxWeight * (curWeight / (curWeight + prevWeight)) + prevMax * (prevWeight / (curWeight + prevWeight))) # max because you can't be weaker than the weight you just lifted...duh
        
        iLiftName = ''
        for tLift in todayLift:
            tLiftWeight, unitLabel = fixUnit(tLift['weight'], unitId)
            iLiftName = iLiftName+'<br />'+str(tLift['sets'])+'x'+str(tLift['reps'])+'x'+str(round(tLiftWeight, 1))+' '+unitLabel
        iMaxName = str(int(round(iMaxWeight, 0)))+' '+unitLabel
        sessionLink = reverse(share.views.blogSession, kwargs = {'sessionid': iLift['session_id']})
        
        workSetData.append({ 'name': iLiftName, 'x': int(unixDate), 'y': iLiftWeight, 'link': sessionLink })
        estMaxData.append({ 'name': iMaxName, 'x': int(unixDate), 'y': iMaxWeight, 'link': sessionLink })
        
        prevDate = iDate
        prevMax = iMaxWeight
    
    return (workSetData, estMaxData)