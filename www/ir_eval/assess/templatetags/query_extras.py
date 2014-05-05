from django import template
from assess.models import *

register = template.Library()

@register.filter(name='done_count')
def done_count(value) :
  return Assessment.objects.filter(query=value, has_assessed=True).count()

@register.filter(name='left_count')
def left_count(value) :
  return Assessment.objects.filter(query=value, has_assessed=False).count()

@register.filter(name='total_count')
def total_count(value) :
  return Assessment.objects.filter(query=value).count()

@register.filter(name='all_done')
def all_done(value) :
  done_count = Assessment.objects.filter(query=value,has_assessed=True).count()
  all_count = Assessment.objects.filter(query=value).count()
  return done_count == all_count