from django.forms import *
from userstats.models import *
from django.contrib.auth.forms import *

class UserForm(ModelForm):
	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'email', )
	
	def __init__(self, *args, **kwargs):
		super(UserForm, self).__init__(*args, **kwargs)
		self.fields['email'].required = True
	
	def clean_email(self):
		email = self.cleaned_data.get('email')
		username = self.save(commit = False).username
		if email and User.objects.filter(email = email).exclude(username = username).count():
			raise forms.ValidationError(u'A user with that email already exists.')
		return email

class UserProfileForm(ModelForm):
	class Meta:
		model = UserProfile
		exclude = ('user', )

class MyUserCreationForm(UserCreationForm):
	email = EmailField()
	
	def clean_email(self):
		email = self.cleaned_data.get('email')
		username = self.cleaned_data.get('username')
		if email and User.objects.filter(email = email).exclude(username = username).count():
			raise forms.ValidationError(u'A user with that email already exists.')
		return email