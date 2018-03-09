from datetime import datetime, timedelta
import time
from time import mktime
import math
import csv

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.db.models import Max
from django.contrib.auth.decorators import login_required

from graphos.sources.model import ModelDataSource
from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart

from .models import DepthMeasurement, OutflowMeasurement, DepthMeasurementDataSource, OutflowMeasurementDataSource, FillRateDataSource, SENSOR_ELEVATION, StorageDataSource
from .forms import ChartForm

def calculate_fill_rate(qs):
    data_pairs = [[m.stamp, m.value] for m in qs]
    #for k, v in data_pairs:
        #print(k, v)
    l = len(data_pairs)
    derivative = []
    for p in range(l):
        try:
            t0 = data_pairs[p][0]
            t1 = data_pairs[p+1][0]
            v0 = data_pairs[p][1]
            v1 = data_pairs[p+1][1]
        except IndexError:
            continue
        if t1 != t0:
            deltat = t1 - t0
            days = deltat.total_seconds()/60.0/1440.0
            fill_change = v1 - v0
            #print(t0, fill_change)
            d = (v1 - v0)/days
            #print(d)
            derivative.append([t0,d])
    #for k, v in derivative:
        #print(k, v)
    avg_4hr = []
    ld = len(derivative)
    for q in range(ld):
        j = q + 4*4
        if j > ld:
            continue
        try:
            sublist = derivative[q:j]
            #for k, v in sublist:
                #print(k, v)
            time = sublist[0][0]
            subtotal = 0
            subl = len(sublist)
            #print(subl)
            for x in range(subl):
                pair = sublist[x]
                value = pair[1]
                subtotal += value
            avg_4hr.append([time, subtotal/subl])
        except IndexError:
            continue
    for k, v in avg_4hr:
        print(k, v)
    return avg_4hr



def get_start_time(request):
    start_time = datetime(2017, 6, 18, 12)
    begin_date = request.GET.get('begin_date')
    if not begin_date:
        chart_form = ChartForm({'begin_date':start_time})
        begin_date = start_time.strftime("%m/%d/%Y")
    else:
        chart_form = ChartForm(request.GET)
    if chart_form.is_valid():
        begin_dt = datetime.fromtimestamp(mktime(time.strptime(begin_date, '%m/%d/%Y')))
        start_time = begin_dt
    return start_time, chart_form

def get_startend_time(request):
    start_time = datetime.today() - timedelta(days=30)
    end_time = datetime.today()
    begin_date = request.GET.get('begin_date')
    end_date = request.GET.get('end_date')
    if not begin_date:
        chart_form = ChartForm({'begin_date':start_time})
        begin_date = start_time.strftime("%m/%d/%Y")
        end_date = end_time.strftime("%m/%d/%Y")
    else:
        chart_form = ChartForm(request.GET)
    if chart_form.is_valid():
        begin_dt = datetime.fromtimestamp(mktime(time.strptime(begin_date, '%m/%d/%Y')))
        end_dt = datetime.fromtimestamp(mktime(time.strptime(end_date, '%m/%d/%Y')))
        start_time = begin_dt
        end_time = end_dt
    return start_time, end_time, chart_form

def get_chart(qs, data_source_class, title, vmax, vmin):
    vaxisoptions = {'viewWindow': {'max': vmax, 'min': vmin}}
    chartareaoptions = {'left':60,'right':20, 'top':50, 'bottom':100}#{'width': '80%', 'height': '80%'}
    legendoptions = {'position': 'bottom'}
    options = {'height':'100%', 'width':'100%', 'vAxis':vaxisoptions, 'title':title, 'chartArea':chartareaoptions, 'legend':legendoptions}
    try:
        chart = LineChart(data_source_class(queryset=qs, fields=['stamp','value']), options=options)#, height=1000, width=1500)
    except TypeError:
        chart = LineChart(data_source_class(data=qs), options=options)
    return chart
    
    
#  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% view functions

def test(request):
    context = {}
    template = 'datafetch/text.html'
    return render(request, template, context)


    

def index(request):
    context = {}
    template = 'datafetch/index.html'
    return render(request, template, context)

def contact(request):
    context = {}
    template = 'datafetch/contact.html'
    return render(request, template, context)
    
@login_required
def depth_chart(request):
    request.session['alldata']={}
    request.session['dataname'] = "LEDE_depth_measurements"
    seshdata = request.session['alldata']
    #start_time, chart_form = get_start_time(request)
    start_time, end_time,  chart_form = get_startend_time(request)
    #qs = DepthMeasurement.objects.filter(stamp__gt=start_time).order_by('stamp')
    end_time = end_time + timedelta(0, 0, 0, 0, 59, 23)
    print(start_time, end_time)
    qs = DepthMeasurement.objects.filter(stamp__gt=start_time, stamp__lte=end_time).order_by('stamp')
    
    for dm in qs:
        seshdata.update({dm.stamp.strftime('%x %X'): dm.value})
    #for k, v in seshdata.items():
        #print('seshdata', k, v)
    #print(len(request.session['alldata']))
    vmax = max([dm.value for dm in qs])#max_height + SENSOR_ELEVATION
    #print('vmax', vmax)
    vmin = min([dm.value for dm in qs])#math.floor(earliest_height + SENSOR_ELEVATION)
    vdiff = vmax - vmin
    vmax = math.ceil(vmax + 0.05*vdiff +  SENSOR_ELEVATION)
    vmin = math.floor(vmin - 0.05*vdiff + SENSOR_ELEVATION)
    vaxisoptions = {'viewWindow': {'max': vmax, 'min': vmin}, 'title': 'Feet'}
    chartareaoptions = {}#{'left':60,'right':20, 'top':50, 'bottom':100}#{'width': '80%', 'height': '80%'}
    legendoptions = {'position': 'bottom'}
    themeoptions = None
    options = {
        'height':'100%',
        'width':'100%',
        'vAxis':vaxisoptions,
        'title':'Reservoir Surface Elevation',
        'chartArea':chartareaoptions,
        'legend':legendoptions,
        'theme':themeoptions
    }
    chart = LineChart(DepthMeasurementDataSource(queryset=qs, fields=['stamp','value']), options=options)#, height=1000, width=1500)
    
    #chart = get_chart(qs, DepthMeasurementDataSource, 'Reservoir Surface Elevation', vmax=max_height + SENSOR_ELEVATION, vmin=math.floor(earliest_height + SENSOR_ELEVATION))
    context = {
        'chart': chart,
        'form':chart_form,
        'current_date':start_time.strftime('%m/%d/%Y'),
        'end_date':end_time.strftime('%m/%d/%Y'),
    }
    template = 'datafetch/depth_chart.html'
    return render(request, template, context)

    
@login_required
def outflow_chart(request):
    start_time, chart_form = get_start_time(request)
    qs = OutflowMeasurement.objects.filter(stamp__gt=start_time).order_by('stamp')
    chart = get_chart(qs, OutflowMeasurementDataSource, 'Outflow Flume Depth', vmax=.5, vmin=0)
    context = {'chart': chart, 'chart_form': chart_form, 'current_date': start_time.strftime('%m/%d/%Y')}
    template = 'datafetch/outflow_chart.html'
    return render(request, template, context)

    
@login_required
def fill_rate(request):
    start_time, chart_form = get_start_time(request)
    depth_qs = DepthMeasurement.objects.filter(stamp__gt=start_time).order_by('stamp')    
    latest_date = depth_qs.latest('stamp').stamp
    depth_qs = depth_qs.filter(stamp__lt=latest_date).order_by('stamp')
    avg_4hr = calculate_fill_rate(depth_qs)
    data_head = ['Time', 'Value']
    simple_source = [data_head]
    for pair in avg_4hr:
        simple_source.append([pair[0],pair[1]])
    chart = get_chart(simple_source, FillRateDataSource, '4-hour Average Fill Rate. Units: feet per day', vmax=2, vmin=-2)
    context = {'chart': chart, 'chart_form': chart_form, 'current_date': start_time.strftime('%m/%d/%Y')}
    #print(avg_4hr)
    template = 'datafetch/fill_rate.html'
    return render(request, template, context)
    
@login_required    
def storage_chart(request):
    start_time, chart_form = get_start_time(request)
    qs = DepthMeasurement.objects.filter(stamp__gt=start_time).order_by('stamp')
    avg_4hr = calculate_fill_rate(qs)
    avgrates = [v for k,v in avg_4hr]
    minmax = [0, 2]
    maxrate = 0
    for a in avgrates:
        if a > maxrate and minmax[0] < a < minmax[1]:
            maxrate = a
    avg_avg = maxrate
    latest_date = qs.latest('stamp').stamp
    earliest_height = qs.earliest('stamp').value
    delta_t = latest_date - start_time
    delta_t = delta_t.total_seconds()/86400 # seconds to days
    max_height = avg_avg*delta_t + earliest_height
    chart = get_chart(qs, StorageDataSource, 'Reservoir Storage', vmax=1200, vmin=0)
    context = {'chart': chart, 'form':chart_form, 'current_date':start_time.strftime('%m/%d/%Y')}
    template = 'datafetch/storage_chart.html'
    #raise Exception
    return render(request, template, context)
    
def download(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % request.session['dataname']

    writer = csv.writer(response)
    for row in request.session['alldata'].items():
        writer.writerow(row)

    return response
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
