from django.db import models
from django.contrib.auth.models import User
from traininglog.models import Session

class SessionComment(models.Model):
    PUBLISHED = 1
    DELETED = 2
    comment_status = (
        (PUBLISHED, 'Published'),
        (DELETED, 'Deleted'),
    )
    session = models.ForeignKey(Session)
    author = models.ForeignKey(User)
    content = models.TextField()
    create_time = models.DateTimeField()
    status = models.IntegerField(choices = comment_status)
    
    class Meta:
        ordering = ['create_time']
    
    def __unicode__(self):
        return "%s's comment, %s" % (self.author, self.session)
    
    def link(self):
        return '/share/blog/session/%s/#c%s' % (self.session_id, self.id)


class Team(models.Model):
    name = models.CharField(max_length = 255)
    pretty_name = models.CharField(max_length = 255)
    description = models.TextField(blank = True)
    members = models.ManyToManyField(User, through = 'TeamMembership')
    
    def __unicode__(self):
        return self.name
    
    def getStatus(self, user):
        if user.is_authenticated():
            if TeamMembership.objects.filter(team = self, user = user).exclude(type = TeamMembership.INVITED).count() > 0:
                return TeamMembership.objects.get(team = self, user = user).type
        return 0 # default code for not a member
        
        
class TeamMembership(models.Model):
    user = models.ForeignKey(User)
    team = models.ForeignKey(Team)
    
    CAPTAIN = 1
    MEMBER = 2
    WANNABE = 3
    INVITED = 4
    TYPE_LIST = (
        (CAPTAIN, 'Captain'),
        (MEMBER, 'Member'),
        (WANNABE, 'Wannabe'),
        (INVITED, 'Invited'),
    )
    type = models.IntegerField(choices = TYPE_LIST)
    
    def __unicode__(self):
        return 'User: %s, Team: %s Membership' % (self.user, self.team)


class TeamInvitation(models.Model):
    team = models.ForeignKey(Team)
    invited_by = models.ForeignKey(User)
    email = models.EmailField()
    
    def __unicode__(self):
        return "%s's invitation to %s" % (self.email, self.team)