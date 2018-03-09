import math

from django.db import models

# Create your models here.

from graphos.sources.model import ModelDataSource
from graphos.sources.model import SimpleDataSource
from graphos.renderers import gchart

from LEDE_config import *



class Measurement(models.Model):
    stamp = models.DateTimeField()
    value = models.FloatField()
    name = models.CharField(max_length=64)
    
    class Meta:
        unique_together = (("stamp", "name"),)
    

class DepthMeasurement(models.Model):
    stamp = models.DateTimeField(unique=True)
    value = models.FloatField()

    def __str__(self):
        return self.stamp.strftime("%x %X ") + str(self.value) + ' ft'

class DepthMeasurementDataSource(ModelDataSource):
    def get_data(self):
        data = super(DepthMeasurementDataSource, self).get_data()
        header = data[0]
        data_without_header = data[1:]
        new_list = []
        for i, row in enumerate(data_without_header):
            k = row[0]
            v = row[1]
            if DEPTH_MIN_VALUE < v < DEPTH_MAX_VALUE:
                new_list.append([k,v + SENSOR_ELEVATION])
        return new_list

class CustomGchart(gchart.LineChart):
    def get_template(self):
        return "demo/gchart_line.html"

class OutflowMeasurement(models.Model):
    stamp = models.DateTimeField(unique=True)
    value = models.FloatField()

    def __str__(self):
        return self.stamp.strftime("%x %X ") + str(self.value) + ' ft'
    
class OutflowMeasurementDataSource(ModelDataSource):
    def get_data(self):
        data = super(OutflowMeasurementDataSource, self).get_data()
        header = data[0]
        data_without_header = data[1:]
        new_list = []
        for i, row in enumerate(data_without_header):
            k = row[0]
            v = row[1]
            if OUTFLOW_MIN_VALUE < v < OUTFLOW_MAX_VALUE:
                new_list.append([k,v])
        return new_list
    
class FillRateDataSource(SimpleDataSource):
    def get_data(self):
        data = super(FillRateDataSource, self).get_data()
        header = data[0]
        data_without_header = data[1:]
        new_list = []
        for i, row in enumerate(data_without_header):
            k = row[0]
            v = row[1]
            if FILLRATE_MIN_VALUE < row[1] < FILLRATE_MAX_VALUE:
                new_list.append([k,v])
        #data_without_header.insert(0, header)
        return new_list

class StorageDataSource(DepthMeasurementDataSource):
    def get_data(self):
        data = super(StorageDataSource, self).get_data()
        newlist = []
        for k, v in data:
            low = math.floor(v)
            high = math.ceil(v)
            try:
                lowstor = STORAGE_VOLUME[low]
                highstor = STORAGE_VOLUME[high]
            except KeyError as e:
                print('key',e,'does not exists')
                return [[]]
            current_rate = highstor - lowstor   
            curstor = lowstor + (v - low)*current_rate
            newlist.append([k,curstor])
        return newlist
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
