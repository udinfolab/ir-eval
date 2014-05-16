from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
  url(r'^$', 'assess.views.home', name='assess_home'),
  url(r'^start$', 'assess.views.start', name='assess_start'),
  url(r'^query/(?P<query_id>\d+)$', 'assess.views.query',
    name='assess_query'),
  url(r'^assessment/(?P<assessment_id>\d+)$', 'assess.views.assessment',
    name='assess_assessment'),
  url(r'^label/(?P<assessment_id>\d+)$', 'assess.views.label',
    name='assess_label'),
  url(r'^raw/(?P<doc_id>\d+)$', 'assess.views.raw',
    name='assess_raw'),
  url(r'^eval/summary$', 'assess.views.eval_summary',
    name='assess_eval_summary'),
  url(r'^eval/(?P<rf_id>\d+)$', 'assess.views.eval_rf',
    name='assess_eval_rf'),
  
  url(r'^login/$', 'django.contrib.auth.views.login',
      {'template_name': 'login.html'}, name='assess_login'),
  url(r'^logout/$', 'assess.views.assessor_logout', name='assess_logout'),
)
