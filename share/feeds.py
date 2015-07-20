from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth.models import User
from traininglog.models import *
from share.models import *
from userstats.models import *

IS_POST = 1
IS_COMMENT = 2
N_FEED_COUNT = 20
MAX_LEN_CONTENT = 500

def buildFeedList(sessionList, commentList):
	iPost = 0
	iComment = 0
	feedList = []
	for iFeed in range(N_FEED_COUNT):
		if iComment < len(commentList) and iPost < len(sessionList):
			if sessionList[iPost].create_time >= commentList[iComment].create_time:
				feedList.append({ 'type': IS_POST, 'obj': sessionList[iPost] })
				iPost += 1
			else:
				feedList.append({ 'type': IS_COMMENT, 'obj': commentList[iComment] })
				iComment += 1
		elif iComment >= len(commentList) and iPost < len(sessionList):
			feedList.append({ 'type': IS_POST, 'obj': sessionList[iPost] })
			iPost += 1
		elif iComment < len(commentList) and iPost >= len(sessionList):
			feedList.append({ 'type': IS_COMMENT, 'obj': commentList[iComment] })
			iComment += 1
		else:
			1 # Do nothing...iterate until counter is dead
	return feedList

class RssAllFeed(Feed):
	title = "I Dream of Steel"
	link = "/"
	description = "Strength training log entries"
	
	def items(self):
		allSession = Session.objects.filter(status = Session.CONFIRMED, author__userprofile__privacy = UserProfile.PUBLIC).order_by('-create_time')
		allComment = SessionComment.objects.filter(session__id__in = allSession.values_list('id', flat = True), status = SessionComment.PUBLISHED).order_by('-create_time')
		return buildFeedList(allSession, allComment)
	
	def item_title(self, item):
		if item['type'] == IS_COMMENT:
			return "%s's comment on %s" % (item['obj'].author, item['obj'].session.title)
		else:
			return "(%s) %s" % (item['obj'].author, item['obj'].title)
		return 'If you see this, report an error to admin@idreamofsteel.com.'
	
	def item_link(self, item):
		if item['type'] == IS_COMMENT:
			return item['obj'].link()
		else:
			return reverse('share.views.blogSession', kwargs = { 'sessionid': item['obj'].id })
		return '/'
	
	def item_description(self, item):
		if len(item['obj'].content) > MAX_LEN_CONTENT:
			return '%s [...]' % item['obj'].content[:MAX_LEN_CONTENT]
		else:
			return item['obj'].content
		return 'If you see this, report an error to admin@idreamofsteel.com.'
	

# The following should probably be collapsed into one function with the functions above, but it's separate now because I want to just get something done

class RssTeamFeed(RssAllFeed):
	def get_object(self, request, team):
		return get_object_or_404(Team, name = team)
	
	def title(self, obj):
		return "I Dream of Steel: %s's Log" % obj.pretty_name
	
	def link(self, obj):
		return reverse('share.views.blogTeam', kwargs = { 'teamname': obj.name, 'page': 1 })
	
	def description(self, obj):
		return "Strength training log entries for %s" % obj.pretty_name
	
	def items(self, obj):
		allSession = Session.objects.filter(Q(status = Session.CONFIRMED) & Q(author__team__id = obj.id) & (Q(author__teammembership__type = TeamMembership.MEMBER) | Q(author__teammembership__type = TeamMembership.CAPTAIN))).exclude(author__userprofile__privacy = UserProfile.PRIVATE).order_by('-create_time')
		allComment = SessionComment.objects.filter(session__id__in = allSession.values_list('id', flat = True), status = SessionComment.PUBLISHED).order_by('-create_time')
		return buildFeedList(allSession, allComment)


class RssUserFeed(RssAllFeed):
	def get_object(self, request, username):
		return get_object_or_404(User, username = username)
	
	def title(self, obj):
		return "I Dream of Steel: %s's Log" % obj.username
	
	def link(self, obj):
		return reverse('share.views.blogUser', kwargs = { 'username': obj.username, 'page': 1 })
	
	def description(self, obj):
		return "Strength training log entries for %s" % obj.username
	
	def items(self, obj):
		allSession = Session.objects.filter(status = Session.CONFIRMED, author = obj).order_by('-create_time')
		allComment = SessionComment.objects.filter(session__id__in = allSession.values_list('id', flat = True), status = SessionComment.PUBLISHED).order_by('-create_time')
		return buildFeedList(allSession, allComment)