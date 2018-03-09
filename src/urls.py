from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^siteview/(?P<sitename>[^/]+)/$', views.site_view, name='site_view'),
    url(r'^siteview/(?P<sitename>[^/]+)/sensors/(?P<sensor_id>[0-9]+)/$', views.sensor_view, name='sensor_view'),
    url(r'^siteview/downloadcsv', views.download, name='download_view'),
] 
