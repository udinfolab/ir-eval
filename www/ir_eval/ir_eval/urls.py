from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ir_eval.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^assess/', include('assess.urls', app_name='assess')),

    url(r'^admin/', include(admin.site.urls)),
)
