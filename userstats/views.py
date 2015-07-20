from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth import authenticate, login, views
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from idreamofsteel.constants import *
from idreamofsteel.util import *
from userstats.forms import *
from userstats.models import *
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from operator import add

WEIGHT_LIST = ['weight',
                'squat_meet', 'bench_meet', 'dead_meet', 'total_meet', 'squat_gym', 'bench_gym', 'dead_gym', 'total_gym',
                'snatch_meet', 'cnj_meet', 'olytotal_meet', 'press_meet', 'snatch_gym', 'cnj_gym', 'olytotal_gym', 'press_gym']

def profileConvertToKgs(input):
    for iWeight in WEIGHT_LIST:
        if input.__dict__[iWeight]:
            input.__dict__[iWeight] = input.__dict__[iWeight] / LBS_PER_KG
    return input

def profileConvertToLbs(input):
    for iWeight in WEIGHT_LIST:
        if input.__dict__[iWeight]:
            input.__dict__[iWeight] = input.__dict__[iWeight] * LBS_PER_KG
    return input


def tupProfile(request, username):
    thisAccount = get_object_or_404(User, username = username)
    if request.user.is_authenticated() and request.user.profile.units == UserProfile.METRIC:
        thisProfile = profileConvertToKgs(thisAccount.profile)
        unit = 'kg'
    else:
        thisProfile = thisAccount.profile
        unit = 'lb'
    return thisAccount, thisProfile, unit
    
    
def idosLogin(request):
    if request.user.is_authenticated():
        return redirect('/')
    try:
        if request.POST['loginType'] == 'Log In':
            return views.login(request)
        else:
            return redirect('/accounts/login/')
    except:
        return render_to_response('registration/login.html', context_instance = RequestContext(request))


@login_required
def editProfile(request):
    thisAccount, thisProfile, unit = tupProfile(request, request.user.username)
    
    userid = thisAccount.id
    chartData = chartProfileData(request, thisProfile)
    
    thisAccount = UserForm(instance = thisAccount, prefix = 'account')
    thisProfile = UserProfileForm(instance = thisProfile, prefix = 'profile')
    
    return render_to_response("registration/profileEdit.html", { 'thisAccount': thisAccount, 'thisProfile': thisProfile, 'unit':  unit, 'chartData': chartData }, context_instance = RequestContext(request))


def viewProfile(request, username):
    thisAccount, thisProfile, unit = tupProfile(request, username)
    
    userid = thisAccount.id
    chartData = chartProfileData(request, thisProfile)
    
    if thisProfile.privacy == UserProfile.PRIVATE:
        return render_to_response("403.html", context_instance = RequestContext(request))
    else:
        return render_to_response("registration/profileView.html", { 'thisAccount': thisAccount, 'thisProfile': thisProfile, 'unit': unit, 'chartData': chartData }, context_instance = RequestContext(request))


def submitProfile(request):
    tempAccount = get_object_or_404(User, pk = request.user.id)
    tempProfile = tempAccount.profile
    
    chartData = chartProfileData(request, tempProfile)
    
    thisAccount = UserForm(request.POST, instance = tempAccount, prefix = 'account')
    thisProfile = UserProfileForm(request.POST, instance = tempProfile, prefix = 'profile')
    
    if thisAccount.is_valid() and thisProfile.is_valid():
        thisAccount.save()
        thisProfile = thisProfile.save(commit = False)
        if thisProfile.units == UserProfile.METRIC:
            thisProfile = profileConvertToLbs(thisProfile)
        thisProfile.save()
        thisProfile = UserProfileForm(instance = thisProfile, prefix = 'profile')
        return redirect('/accounts/profile/edit/?profileChange=1')
    else:
        if tempProfile.units == UserProfile.METRIC:
            unit = 'kg'
        else:
            unit = 'lb'
        # this is somewhat redundant with the code above. Find a way to DRY?
        return render_to_response("registration/profileEdit.html", { 'thisAccount': thisAccount, 'thisProfile': thisProfile, 'unit':  unit, 'chartData': chartData }, context_instance = RequestContext(request))


def createUser(request):
    creationForm = MyUserCreationForm(request.POST)
    if creationForm.is_valid():
        newUser = User.objects.create_user(creationForm.cleaned_data['username'], creationForm.cleaned_data['email'], creationForm.cleaned_data['password1'])
        authUser = authenticate(username = creationForm.cleaned_data['username'], password = creationForm.cleaned_data['password1'])
        login(request, authUser)
        return redirect('/accounts/profile/edit/?newUser=1')
    else:
        return render_to_response('registration/login.html', { 'creationForm': creationForm }, context_instance = RequestContext(request))


def getClassLiftAll(userWeight, classIndex, units = UserProfile.IMPERIAL, sex = UserProfile.MALE):
    # Returns the weights for every lift of a certain class as a list. See getClassLiftWeight for more details
    sigFig = 1
    wList = [round(getClassLiftWeight(userWeight, classIndex, SQUAT_CLASS[sex], units), sigFig),
             round(getClassLiftWeight(userWeight, classIndex, BENCH_CLASS[sex], units), sigFig),
             round(getClassLiftWeight(userWeight, classIndex, DEADLIFT_CLASS[sex], units), sigFig),
             round(getClassLiftWeight(userWeight, classIndex, SNATCH_CLASS[sex], units), sigFig),
             round(getClassLiftWeight(userWeight, classIndex, CNJ_CLASS[sex], units), sigFig),
             round(getClassLiftWeight(userWeight, classIndex, PRESS_CLASS[sex], units), sigFig)]
    return wList


def chartProfileData(request, profile):
    
    if request.user.is_authenticated():
        units = request.user.profile.units
    else:
        units = UserProfile.IMPERIAL
    
    label = ['Squat', 'Bench Press', 'Deadlift', 'Snatch', 'Clean & Jerk', 'Press']
    meet = [Z(profile.squat_meet), Z(profile.bench_meet), Z(profile.dead_meet), Z(profile.snatch_meet), Z(profile.cnj_meet), Z(profile.press_meet)]
    gym = [Z(profile.squat_gym), Z(profile.bench_gym), Z(profile.dead_gym), Z(profile.snatch_gym), Z(profile.cnj_gym), Z(profile.press_gym)]
    
    fLabel = []
    fMeet = []
    fGym = []
    for iLift in range(len(meet)):
        if meet[iLift] != 0 or gym[iLift] != 0:
            fLabel.append(label[iLift])
            fMeet.append(meet[iLift])
            fGym.append(gym[iLift])
    
    fElite = []
    fAdvanced = []
    fIntermediate = []
    fNovice = []
    fUntrained = []
    if profile.weight is not None:
        elite = getClassLiftAll(profile.weight, ELITE, units, profile.sex)
        advanced = getClassLiftAll(profile.weight, ADVANCED, units, profile.sex)
        intermediate = getClassLiftAll(profile.weight, INTERMEDIATE, units, profile.sex)
        novice = getClassLiftAll(profile.weight, NOVICE, units, profile.sex)
        untrained = getClassLiftAll(profile.weight, UNTRAINED, units, profile.sex)
        for iLift in range(len(meet)):
            if meet[iLift] != 0 or gym[iLift] != 0:
                fElite.append(elite[iLift])
                fAdvanced.append(advanced[iLift])
                fIntermediate.append(intermediate[iLift])
                fNovice.append(novice[iLift])
                fUntrained.append(untrained[iLift])
    
    absolute = { 'label': fLabel, 'meet': fMeet, 'gym': fGym, 'elite': fElite, 'master': fAdvanced, 'advanced': fIntermediate, 'intermediate': fNovice, 'novice': fUntrained }
    relative = absolute
    
    chartData = { 'absolute': absolute, 'relative': relative }
    
    return chartData