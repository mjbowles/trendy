from django.contrib import admin

# Register your models here.

from .models import TimeSeriesDataSet, Site, Instrument, Sensor, TSDatum, TSDSCalibration

class TimeSeriesDataSetAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        data = obj.tsdatum_set.all()
        #print('calling save')
        for tsd in data:
            #print('looping')
            if obj.maxval and obj.maxval < tsd.value:
                tsd.delete()
            if obj.minval and obj.minval > tsd.value:
                tsd.delete()
        obj.save()

admin.site.register(TimeSeriesDataSet, TimeSeriesDataSetAdmin)



admin.site.register(Site)
admin.site.register(Instrument)
admin.site.register(Sensor)
admin.site.register(TSDatum)
admin.site.register(TSDSCalibration)
