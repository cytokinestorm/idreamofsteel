from traininglog.models import *
from share.models import *
from django.contrib import admin

class StrengthInline(admin.TabularInline):
	model = Strength
	extra = 1

class CommentInline(admin.TabularInline):
	model = SessionComment
	extra = 1

class SessionAdmin(admin.ModelAdmin):
	fields = ['author', 'create_time', 'session_date', 'status', 'title', 'content']
	inlines = [StrengthInline, CommentInline]
	list_display = ('title', 'author', 'session_date')
	list_filter = ['session_date']
	search_fields = ['title', 'content']
	date_hierarchy = 'session_date'

class ExerciseLookupAdmin(admin.ModelAdmin):
	list_display = ('name', 'user')

admin.site.register(Session, SessionAdmin)
admin.site.register(ExerciseLookup, ExerciseLookupAdmin)