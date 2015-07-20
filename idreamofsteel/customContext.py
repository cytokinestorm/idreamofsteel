import datetime
from idreamofsteel.settings import REVISION

def revision(request):
	return { 'REVISION': REVISION }