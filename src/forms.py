
from django import forms
from django.contrib.admin.widgets import AdminDateWidget

class ChartForm(forms.Form):
    begin_date = forms.DateField(widget=AdminDateWidget)
