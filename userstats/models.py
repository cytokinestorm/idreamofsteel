from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from idreamofsteel.constants import *

class UserProfile(models.Model):
    user = models.OneToOneField(User)

    MALE = MALE # Import from idreamofsteel.constants
    FEMALE = FEMALE
    sexList = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    )
    sex = models.IntegerField(choices = sexList, default = MALE)

    METRIC = 1
    IMPERIAL = 2
    unitsList = (
        (METRIC, 'Metric (kg)'),
        (IMPERIAL, 'Imperial (lb)'),
    )
    units = models.IntegerField(choices = unitsList, default = IMPERIAL)

    PRIVATE = 1
    TEAM_PUBLIC = 2
    PUBLIC = 3
    privacyList = (
        (PRIVATE, 'Private'),
        (TEAM_PUBLIC, 'Team Public'),
        (PUBLIC, 'Public'),
    )
    privacy = models.IntegerField(choices = privacyList, default = PUBLIC)

    weight = models.FloatField(blank = True, null = True)
    
    # Powerlifting
    pl_weightclass = models.IntegerField(choices = PL_WEIGHTCLASSNAME, blank = True, null = True)
    squat_meet = models.FloatField(blank = True, null = True)
    bench_meet = models.FloatField(blank = True, null = True)
    dead_meet = models.FloatField(blank = True, null = True)
    total_meet = models.FloatField(blank = True, null = True)
    squat_gym = models.FloatField(blank = True, null = True)
    bench_gym = models.FloatField(blank = True, null = True)
    dead_gym = models.FloatField(blank = True, null = True)
    total_gym = models.FloatField(blank = True, null = True)
    
    # Olympic lifting
    oly_weightclass = models.IntegerField(choices = OL_WEIGHTCLASSNAME, blank = True, null = True)
    snatch_meet = models.FloatField(blank = True, null = True)
    cnj_meet = models.FloatField(blank = True, null = True)
    press_meet = models.FloatField(blank = True, null = True)
    olytotal_meet = models.FloatField(blank = True, null = True)
    snatch_gym = models.FloatField(blank = True, null = True)
    cnj_gym = models.FloatField(blank = True, null = True)
    press_gym = models.FloatField(blank = True, null = True)
    olytotal_gym = models.FloatField(blank = True, null = True)
    
    def __str__(self):
        return "%s's profile" % self.user
    
    def get_prettysex(self):
        return dict(self.sexList)[self.sex]
    
    def get_prettyPlClass(self):
        return dict(PL_WEIGHTCLASSNAME)[self.pl_weightclass]
    
    def get_prettyOlyClass(self):
        return dict(OL_WEIGHTCLASSNAME)[self.oly_weightclass]
    
User.profile = property(lambda u: UserProfile.objects.get_or_create(user = u)[0])