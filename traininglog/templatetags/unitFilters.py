from django import template
from idreamofsteel.constants import *
from string import replace
import re

register = template.Library()

@register.filter
def toKgs(input):
	input = float(input)
	input = input / LBS_PER_KG
	return input

@register.filter
def toKgsForm(input):
	input = input.__unicode__()
	regex = re.compile('(?<=value=").*?(?=")')
	searchResult = regex.search(input)
	if searchResult != None:
		lbVal = searchResult.group()
		kgVal = str(float(lbVal) / LBS_PER_KG)
		input = input.replace('value="'+lbVal+'"', 'value="'+kgVal+'"')
	return(input)