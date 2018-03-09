import math

from django.db import models

# Create your models here.

from graphos.sources.model import ModelDataSource
from graphos.sources.model import SimpleDataSource
from graphos.renderers import gchart

SENSOR_ELEVATION = 9499
DEPTH_MIN_VALUE = 0
DEPTH_MAX_VALUE = 100

OUTFLOW_MIN_VALUE = 0
OUTFLOW_MAX_VALUE = 1

FILLRATE_MIN_VALUE = -2
FILLRATE_MAX_VALUE = 2


STORAGE_VOLUME = {  
#   ELEV : ACRE-FEET
    9494 : 0.0,
    9495 : 0.0,
    9496 : 0.0,
    9497 : 3.6,
    9498 : 7.1,
    9499 : 13.7,
    9500 : 20.2,
    9501 : 29.0,
    9502 : 37.9,
    9503 : 48.7,
    9504 : 59.5,
    9505 : 72.2,
    9506 : 84.9,
    9507 : 99.1,
    9508 : 113.4,
    9509 : 129.1,
    9510 : 144.9,
    9511 : 162.1,
    9512 : 179.4,
    9513 : 198.0,
    9514 : 216.5,
    9515 : 236.3,
    9516 : 256.1,
    9517 : 277.1,
    9518 : 298.0,
    9519 : 320.0,
    9520 : 342.1,
    9521 : 342.1,
    9522 : 388.3,
    9523 : 412.6,
    9524 : 436.8,
    9525 : 462.1,
    9526 : 487.4,
    9527 : 513.5,
    9528 : 539.6,
    9529 : 566.5,
    9530 : 593.5,
    9531 : 621.2,
    9532 : 649.0,
    9533 : 677.6,
    9534 : 706.2,
    9535 : 735.7,
    9536 : 765.1,
    9537 : 795.1,
    9538 : 825.9,
    9539 : 857.3,
    9540 : 888.6,
    9541 : 921.0,
    9542 : 953.3,
    9543 : 986.6,
    9544 : 1020.0,
    9545 : 1053.3,
    9546 : 1086.7,
    9547 : 1120.0,
    9548 : 1153.4,
}

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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
