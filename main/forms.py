from django import forms
from .models import Event
from .models import *
from .models import InsurancePurchase

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'date', 'location', 'price', 
                 'total_tickets', 'status', 'image']
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

from django import forms
from .models import Appointment, Doctor

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason', 'consultation_type']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.Select(choices=[
                (f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}")
                for hour in range(8, 18)  # 8 AM to 5 PM
                for minute in [0, 30]  # Every 30 minutes
            ]),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You might want to filter doctors based on availability
        self.fields['doctor'].queryset = Doctor.objects.filter(is_active=True)
        
        # Add dynamic logic for virtual appointments
        self.fields['consultation_type'].widget.attrs.update({
            'class': 'form-select',
            'onchange': 'toggleMeetingLink(this.value)'
        })

class ConsultancyRequestForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your consultancy needs'}))
    preferred_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    preferred_time = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)