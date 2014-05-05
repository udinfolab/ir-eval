import base64
from django import template
from assess.models import *

register = template.Library()

@register.filter(name='b64_decode')
def b64_decode(data) :
  return base64.b64decode(data)

@register.filter(name='short_snippet')
def short_snippet(data) :
  if len(data) > 60 :
    return '%s ...' % data[0:60]
  else :
    return data
