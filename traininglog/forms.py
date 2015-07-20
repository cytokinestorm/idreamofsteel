from django.forms import *
from traininglog.models import *
from idreamofsteel.constants import *

class SessionForm(ModelForm):
    class Meta:
        model = Session
        fields = ('session_date', 'title', 'content', )
        widgets = {'session_date': DateInput(attrs = {'class': 'logDate'}),
                   'title': TextInput(attrs = {'class': 'logTitle', 'placeholder': 'Title'}),
                   'content': Textarea(attrs = {'class': 'logContent'})}

class StrengthForm(ModelForm):
    lift = CharField(widget = TextInput(attrs = {'class': 'liftInput', 'autocomplete': 'off', 'placeholder': 'Type lift name'}))
    
    class Meta:
        model = Strength
        fields = ('sets', 'reps', 'weight', 'mo', 'comments', )
        widgets = {'comments': Textarea(attrs = {'placeholder': 'Additional comments'})}

class logImportForm(Form):
	logFile = FileField()