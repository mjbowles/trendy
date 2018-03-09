from django.db import models

import datetime

from graphos.sources.model import ModelDataSource
from graphos.sources.model import SimpleDataSource
from graphos.renderers import gchart

from django.utils.timezone import now as DJANGO_NOW

class Site(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)
    
class Instrument(models.Model):
    name = models.CharField(max_length=100)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    site = models.ForeignKey('Site', on_delete=models.CASCADE)

    def __str__(self):
        return "{0} at {1}".format(self.name, self.site)

class Sensor(models.Model):
    name = models.CharField(max_length=100)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    instrument = models.ForeignKey('Instrument', on_delete=models.CASCADE)

    def __str__(self):
        return "{0} in {1}".format(self.name, self.instrument)

class TimeSeriesDataSet(models.Model):
    WEIRDEPTH = 'WD'
    BINARY = 'BI'
    TANKLEVEL = 'TL'
    CLLEVEL = 'CL'
    RUNHOURS = 'RH'
    TURBIDITY = 'TU'
    TEMPERATURE = 'TE'
    TSDSTYPECHOICES = (
        (WEIRDEPTH, 'Weir Depth'),
        (BINARY, 'On/Off Status'),
        (TANKLEVEL, 'Tank Level'),
        (CLLEVEL, 'Chlorine Reading'),
        (RUNHOURS, 'Run Hours'),
        (TURBIDITY, 'Turbidity Reading'),
        (TEMPERATURE, 'Temperature'),
    )
    description = models.CharField(max_length=255)
    sensor = models.OneToOneField('Sensor', on_delete=models.CASCADE)
    maxval = models.FloatField(null=True, blank=True)
    minval = models.FloatField(null=True, blank=True)
    tsdstype = models.CharField(max_length=100, choices=TSDSTYPECHOICES)
    
    def __str__(self):
        size = self.tsdatum_set.count()
        return '{0} dataset with {1} entries'.format(self.sensor, size)
    
    #def save(self, *args, **kwargs):
        #data = self.tsdatum_set.all()
        #for tsd in data:
            #if self.maxval and self.maxval < tsd.value:
                #tsd.delete()
            #if self.minval and self.minval > tsd.value:
                #tsd.delete()
        #super(TimeSeriesDataSet, self).save(*args, **kwargs)

class TSDatum(models.Model):
    tsds = models.ForeignKey('TimeSeriesDataSet', on_delete=models.CASCADE)
    stamp = models.DateTimeField()
    value = models.FloatField()
    
    class Meta:
        unique_together = ('tsds','stamp')
        
    def __str__(self):
        return '{0}. {1} {2}'.format(self.tsds.sensor, self.stamp, self.value)

class TSDatumDataSource(ModelDataSource):
    def get_data(self):
        data = super(TSDatumDataSource, self).get_data()
        header = data[0]
        data_without_header = data[1:]
        new_list = []
        for i, row in enumerate(data_without_header):
            k = row[0]
            v = row[1]
            #if DEPTH_MIN_VALUE < v < DEPTH_MAX_VALUE:
            new_list.append([k,v])
        return new_list

class CalibratedDataSource(SimpleDataSource):
    def get_data(self):
        data = super(CalibratedDataSource, self).get_data()
        header = data[0]
        data_without_header = data[1:]
        new_list = []
        for i, row in enumerate(data_without_header):
            k = row[0]
            v = row[1]
            #if FILLRATE_MIN_VALUE < row[1] < FILLRATE_MAX_VALUE:
            new_list.append([k,v])
        #data_without_header.insert(0, header)
        return new_list


class TSDSCalibration(models.Model):
    WEIR = 'WEIR'
    SIMPLE = 'SIMPLE'
    CUSTOM = 'CUSTOM'
    CALIBTYPE_CHOICES = (
        (WEIR,'WIER'),
        (SIMPLE,'SIMPLE'),
        (CUSTOM,'CUSTOM'),
    )
    begindate = models.DateTimeField(default=DJANGO_NOW)
    factor = models.FloatField(default=1)
    offset = models.FloatField(default=0)
    units = models.CharField(max_length=100)
    calibtype = models.CharField(max_length=25, choices=CALIBTYPE_CHOICES, default='SIMPLE')
    custom_function = models.CharField(max_length=254, null=True)
    tsds = models.ForeignKey('TimeSeriesDataSet', on_delete=models.CASCADE)
    weira = models.FloatField(null=True, default=1)
    weirb = models.FloatField(null=True, default=0)
    weirc = models.FloatField(null=True, default=0)
    weird = models.FloatField(null=True, default=2.5)

    def calibrate(self, value):
        a = self.weira
        b = self.weirb
        c = self.weirc
        d = self.weird
        if self.calibtype == self.WEIR:
            return a * ((-1)**(b)*value - c)**d
        if self.calibtype == self.SIMPLE:
            return self.factor * value + self.offset

    
        
    def __str__(self):
        return 'Calibration for {0} beginning {1}'.format(self.tsds, self.begindate.strftime('%x'))






















