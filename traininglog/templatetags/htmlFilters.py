from django import template
from string import replace
import re

register = template.Library()

@register.filter
def postFilter(input):
	# I can probably clean this up, but I'm just damned glad that I'm done
	basicTags = ['b', 'i', 'sup', 'sub', 'ul', 'ol', 'li']
	for iTag in basicTags:
		input = input.replace(u'['+iTag+u']', u'<'+iTag+u'>')
		input = input.replace(u'[/'+iTag+u']', u'</'+iTag+u'>')
	
	# Non-one-to-one tag replacements
	input = input.replace(u'[hr]', u'<hr />')
	
	input = input.replace(u'[s]', u'<del>')
	input = input.replace(u'[/s]', u'</del>')
	
	input = input.replace(u'[quote]', u'<blockquote>')
	input = input.replace(u'[/quote]', u'</blockquote>')
	
	input = input.replace(u'[u]', u'<span style="text-decoration: underline">')
	input = input.replace(u'[/u]', u'</span>')
	
	input = input.replace(u'[left]', u'<div style="text-align: left">')
	input = input.replace(u'[/left]', u'</div>')
	
	input = input.replace(u'[right]', u'<div style="text-align: right">')
	input = input.replace(u'[/right]', u'</div>')
	
	input = input.replace(u'[center]', u'<div style="text-align: center">')
	input = input.replace(u'[/center]', u'</div>')
	
	input = input.replace(u'[justify]', u'<div style="text-align: justify">')
	input = input.replace(u'[/justify]', u'</div>')
	
	input = input.replace(u'[size=1]', u'<span style="font-size: 60%">')
	input = input.replace(u'[size=2]', u'<span style="font-size: 85%">')
	input = input.replace(u'[size=3]', u'<span style="font-size: 100%">')
	input = input.replace(u'[size=4]', u'<span style="font-size: 120%">')
	input = input.replace(u'[size=5]', u'<span style="font-size: 150%">')
	input = input.replace(u'[size=6]', u'<span style="font-size: 200%">')
	input = input.replace(u'[size=7]', u'<span style="font-size: 300%">')
	input = input.replace(u'[/size]', u'</span>')
	
	input = re.sub('\[url=(?P<link>.+?)\]', '<a href=\g<link>>', input)
	input = input.replace('[/url]', '</a>')
	
	input = re.sub('\[email=(?P<email>.+?)\]', '<a href="mailto:\g<email>">', input)
	input = input.replace('[/email]', '</a>')
	
	input = re.sub('\[color=(?P<color>.+?)\]', '<span style="color: \g<color>">', input)
	input = input.replace('[/color]', '</span>')
	
	input = re.sub('\[youtube\](?P<video>.+?)\[/youtube\]', '<iframe width="560" height="315" src="http://www.youtube.com/embed/\g<video>?rel=0" frameborder="0" allowfullscreen></iframe>', input)
	
	input = re.sub('\[img=(?P<width>\d+?)x(?P<height>\d+?)\](?P<src>.+?)\[/img\]', '<img src="\g<src>" width=\g<width> height=\g<height> />', input)
	input = re.sub('\[img\](?P<src>.+?)\[/img\]', '<img src="\g<src>" />', input)
	
	return input