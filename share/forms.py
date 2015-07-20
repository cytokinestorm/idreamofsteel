from django.forms import *
from share.models import *

class SessionCommentForm(ModelForm):
	honeypot = CharField(required = False)
	class Meta:
		model = SessionComment
		fields = ('content', )
		

class TeamForm(ModelForm):
	pretty_name = CharField(max_length = 255, widget = forms.TextInput(attrs = { 'placeholder': 'Team Name' }))
	name = RegexField(max_length = 60, regex = r"^[\w.@+-]+$", widget = forms.TextInput(attrs = { 'placeholder': 'Path (i.e. http://www.idreamofsteel/PATH or, in the future, http://PATH.idreamofsteel.com)' }), 
		error_messages = { 'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters." })
	description = CharField(required = False, max_length = 5000, widget = forms.Textarea(attrs = { 'placeholder': 'Team description (max 5000 chars)' }))
	
	class Meta:
		model = Team
		fields = ('pretty_name', 'name', 'description', )
	
	def clean_pretty_name(self):
		pretty_name = self.cleaned_data.get('pretty_name')
		id = self.save(commit = False).id
		if pretty_name and Team.objects.filter(pretty_name = pretty_name).exclude(id = id).count():
			raise forms.ValidationError(u'A team with that name already exists.')
		return pretty_name
	
	def clean_name(self):
		name = self.cleaned_data.get('name')
		id = self.save(commit = False).id
		if name and Team.objects.filter(name = name).exclude(id = id).count():
			raise forms.ValidationError(u'A team with that path already exists.')
		return name