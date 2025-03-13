from django import forms
from .models import Event
from .models import *

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'date', 'price', 
      'image']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
class VendorRegistrationForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['shop_name', 'location']