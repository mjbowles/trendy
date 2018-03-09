import csv

from django.shortcuts import render
from django.http import HttpResponse

from urllib.parse import urlparse, unquote

import timeseries.models

from datetime import datetime, timedelta
import time
from time import sleep
from time import mktime

from graphos.sources.model import ModelDataSource
from graphos.sources.model import SimpleDataSource
from graphos.renderers.gchart import LineChart
from graphos.renderers import gchart

from .forms import ChartForm

def get_chart(qs, data_source_class, title, vmax, vmin):
    vaxisoptions = {}#{'viewWindow': {'max': vmax, 'min': vmin}}
    chartareaoptions = {}#{'left':60,'right':20, 'top':50, 'bottom':100}#{'width': '80%', 'height': '80%'}
    legendoptions = {'position': 'bottom'}
    options = {'height':'100%', 'width':'100%', 'vAxis':vaxisoptions, 'title':title, 'chartArea':chartareaoptions, 'legend':legendoptions}
    try:
        chart = LineChart(data_source_class(queryset=qs, fields=['stamp','value']), options=options)#, height=1000, width=1500)
    except TypeError:
        chart = LineChart(data_source_class(data=qs), options=options)
    return chart
    

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


def index(request):
    allsites = timeseries.models.Site.objects.all()
    context = {'allsites':allsites}
    template = 'timeseries/index.html'
    return render(request, template, context)
    

def find_calib(dtime, calibrations):
    using_calib = None
    for calib in calibrations:
        if calib.begindate <= dtime:
            using_calib = calib
    return using_calib
    
def calculate_avg(data_pairs):
    count = 0
    avg_val_sum = 0
    avgd_source = []
    initial_stamp = data_pairs[1][0]
    cur_hour = initial_stamp.hour
    for stamp, value in data_pairs[1:]:
        if cur_hour == stamp.hour:
            avg_val_sum += value
            count += 1
        else:
            avgd_source.append([initial_stamp, avg_val_sum/count])
            count = 0
            avg_val_sum = 0
            initial_stamp = stamp
            cur_hour = initial_stamp.hour
            avg_val_sum += value
            count += 1
    return avgd_source


def get_average(data_pairs):
    count = 0
    avg_val_sum = 0
    for stamp, value in data_pairs[1:]:
        avg_val_sum += value
        count += 1
    return avg_val_sum/count
    
def get_max(data_pairs):
    maxval = -9999999999999
    for stamp, value in data_pairs[1:]:
        if value > maxval:
            maxval = value
            maxdate = stamp
    return maxdate, maxval
    
def get_min(data_pairs):
    minval = 9999999999999
    for stamp, value in data_pairs[1:]:
        if value < minval:
            minval = value
            mindate = stamp
    return mindate, minval

def site_view(request, sitename):
    request.session['alldata']={}
    seshdata = request.session['alldata']
    start_time, end_time,  chart_form = get_startend_time(request)
    sitename = unquote(sitename)
    print(sitename)
    site = timeseries.models.Site.objects.get(name=sitename)
    instru = site.instrument_set.all()[0]
    allsensors = instru.sensor_set.all()
    charts = []
    vaxisoptions = {}#{'viewWindow': {'max': vmax, 'min': vmin}}
    chartareaoptions = {}#{'left':60,'right':20, 'top':50, 'bottom':100}#{'width': '80%', 'height': '80%'}
    legendoptions = {'position': 'bottom'}
    for sensor in allsensors:
        summary = []
        highlight_points = []
        tsds = sensor.timeseriesdataset
        #print(tsds.tsdatum_set.all())
        qs = tsds.tsdatum_set.filter(stamp__gt=start_time,
                                     stamp__lte=end_time).order_by('stamp')
        calibrations = tsds.tsdscalibration_set.filter(begindate__lt=end_time).order_by('begindate')
        print(tsds, calibrations)
        data_head = ['Time', 'Value']
        simple_source = [data_head]
        using_calib = None
        qs_eval = [[v.stamp,v.value]for v in qs]
        #for pr in qs_eval:
            #print(pr)
        #sleep(15)
        for stamp,val in qs_eval:
            if not using_calib:
                using_calib = find_calib(stamp, calibrations)
            if using_calib and using_calib.begindate >= stamp:
                using_calib = find_calib(stamp, calibrations)
            if using_calib:
                val = using_calib.calibrate(val)
            if val or val==0:
                simple_source.append([stamp,val])
        #for p in calculate_avg(simple_source):
            #print(p)
        maxdate, maxval = get_max(simple_source)
        mmstring = '{0} on {1} at {2}'
        maxstring = mmstring.format(
                maxval, maxdate.strftime('%x'), maxdate.strftime('%X'))
        summary.extend([
            ['Average', get_average(simple_source)],
            ['Maximum', maxstring],
        ])
        maxpointrows = [{
            'stamp':maxdate,
            'nulls':"null,",
            'value':maxval,
        }]
        maxhp = {
            'type':"number",
            'label':"Maximum",
            'rows':maxpointrows,
        }
        mindate, minval = get_min(simple_source)
        minstring = mmstring.format(
                minval, mindate.strftime('%x'), mindate.strftime('%X'))
        summary.extend([
            ['Minimum', minstring],
        ])
        minpointrows = [{
            'stamp':mindate,
            'nulls':"null,"*2,
            'value':minval,
        }]
        minhp = {
            'type':"number",
            'label':"Minimum",
            'rows':minpointrows,
        }
        highlight_points.append(maxhp)
        highlight_points.append(minhp)
        options = {
            'vAxis':vaxisoptions, 
            'title':str(sensor),
            'chartArea':chartareaoptions, 
            'legend':legendoptions
        }
        dataname = str(sensor)
        simple_source_serialized = []
        for t, v in simple_source[1:]:
            simple_source_serialized.append([t.strftime('%x %X'), v])
        print(simple_source_serialized)
        seshdata.update({dataname : simple_source_serialized})        
        chart = LineChart(
            timeseries.models.CalibratedDataSource(data=simple_source),
            options=options
        )
        chart.summary = summary
        chart.highlights = highlight_points
        charts.append(chart)
    context = {
        'site':site,
        'charts':charts,
        'form': chart_form,
        'current_date':start_time.strftime('%m/%d/%Y'),
        'end_date':end_time.strftime('%m/%d/%Y'),
        'series': {
            '1': { 'lineWidth': 20},
            '2': { 'lineWidth': 20},
        }
    }
    template = 'timeseries/siteview.html'
    return render(request, template, context)
    
def sensor_view(request, sensor_id, **kwargs):
    sensor = timeseries.models.Sensor.objects.get(id=sensor_id)
    tsds = sensor.timeseriesdataset
    qs = tsds.tsdatum_set.all()
    chart = LineChart(timeseries.models.TSDatumDataSource(queryset=qs, fields=['stamp','value']))
    context = {'chart':chart, 'sensor':sensor}
    template = 'timeseries/sensorview.html'
    return render(request, template, context)


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
    chart = get_chart(simple_source, FillRateDataSource, '4-hour Average Fill Rate. Units: feet per day', vmax=2, vmin=0)
    context = {'chart': chart, 'chart_form': chart_form, 'current_date': start_time.strftime('%m/%d/%Y')}
    #print(avg_4hr)
    template = 'datafetch/fill_rate.html'
    return render(request, template, context)
    
def download(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sitename.csv"'

    writer = csv.writer(response)
    for sensor, sensordata in request.session['alldata'].items():
        writer.writerow([sensor])
        for row in sensordata:
            writer.writerow(row)

    return response
























