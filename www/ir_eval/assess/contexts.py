# How to get the name of current app within a template?
# http://stackoverflow.com/a/20021130

from django.core.urlresolvers import resolve
def appname(request):
    return {'appname': resolve(request.path).app_name}