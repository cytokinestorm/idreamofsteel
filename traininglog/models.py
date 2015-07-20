from django.db import models
from django.contrib.auth.models import User

class Session(models.Model):
    CONFIRMED = 1
    PLANNED = 2
    DELETED = 3
    SESSION_STATUS = (
        (CONFIRMED, 'Confirmed'),
        (PLANNED, 'Planned'),
        (DELETED, 'Deleted'),
    )
    
    author = models.ForeignKey(User)
    create_time = models.DateTimeField()
    session_date = models.DateField()
    title = models.CharField(max_length = 255)
    content = models.TextField(blank = True)
    status = models.IntegerField(choices = SESSION_STATUS)
    
    def __unicode__(self):
        return self.title
    
    def fancyMonth(self):
        tMonth = self.session_date.month
        if tMonth < 10:
            return '0'+str(tMonth)
        else:
            return str(tMonth)


class ExerciseLookup(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length = 255)
    
    class Meta:
        ordering = ['name']
    
    def __unicode__(self):
        return self.name


class Strength(models.Model):
    session = models.ForeignKey(Session)
    lift = models.ForeignKey(ExerciseLookup)
    sets = models.IntegerField()
    reps = models.IntegerField()
    weight = models.FloatField()
    mo = models.BooleanField()
    comments = models.TextField(blank = True)
    
    def __unicode__(self):
        return self.lift.name