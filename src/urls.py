from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^depthchart', views.depth_chart, name='depth_chart'),
    url(r'^outflowchart', views.outflow_chart, name='outflow_chart'),
    url(r'^fillrate', views.fill_rate, name='fill_rate'),
    url(r'^test', views.test),
    url(r'^storage', views.storage_chart, name='storage_chart'),
    url(r'^downloadcsv', views.download, name='download_view'),
]
