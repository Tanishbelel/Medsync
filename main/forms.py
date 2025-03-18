from django import forms
from .models import Event
from .models import *
from .models import InsurancePurchase

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


from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, InsuranceInfo

class AppointmentForm(forms.ModelForm):
    """Form for creating a new appointment"""
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'consultation_type', 'reason']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom CSS classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_appointment_date(self):
        date = self.cleaned_data['appointment_date']
        today = timezone.now().date()
        
        if date < today:
            raise forms.ValidationError("Cannot book appointments in the past.")
        
        # Check if date is too far in the future (e.g., more than 3 months)
        if date > today + timedelta(days=90):
            raise forms.ValidationError("Cannot book appointments more than 3 months in advance.")
            
        return date

class InsuranceInfoForm(forms.ModelForm):
    """Form for patient insurance information"""
    
    class Meta:
        model = InsuranceInfo
        fields = ['provider', 'policy_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields not required
        self.fields['provider'].required = False
        self.fields['policy_number'].required = False
        
        # Add custom CSS classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class AppointmentCancellationForm(forms.Form):
    """Form for cancelling an appointment"""
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False
    )
    
    confirm_cancellation = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must confirm the cancellation'}
    )

class InsurancePurchaseForm(forms.ModelForm):
    class Meta:
        model = InsurancePurchase
        fields = ['plan_name', 'coverage_amount', 'monthly_premium']

from django import forms
from .models import PatientProfile

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = '__all__'