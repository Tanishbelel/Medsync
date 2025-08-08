from django.db import models
from django.contrib.auth.models import User
import uuid
from decimal import Decimal
from django.utils import timezone

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20)
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    points = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Student'
    
    def __str__(self):
        return f"{self.user.username} - {self.student_id}"

class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = 'Vendor'
    
    def __str__(self):
        return self.shop_name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=50, unique=True)
    payment_method = models.CharField(max_length=50)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    
    def get_total(self):
        return self.price * self.quantity

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def get_total(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.product_name} - {self.user.username}'s cart"
    
class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled')
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_tickets = models.PositiveIntegerField()
    available_tickets = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.id:
            self.available_tickets = self.total_tickets
        super().save(*args, **kwargs)

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    message = models.TextField()
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
class Specialization(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True)
    profile_picture = models.ImageField(upload_to='doctor_profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['last_name', 'first_name']

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_new_patient = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class InsuranceInfo(models.Model):
    patient = models.OneToOneField(User, on_delete=models.CASCADE, related_name='insurance_info')
    provider = models.CharField(max_length=100)
    policy_number = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True)
    coverage_start_date = models.DateField(null=True, blank=True)
    coverage_end_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.patient.username}'s Insurance"

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('MISSED', 'Missed'),
    )
    
    TYPE_CHOICES = (
        ('in_person', 'In-Person'),
        ('virtual', 'Virtual'),
    )
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.CharField(max_length=5)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    consultation_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='in_person')
    meeting_link = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.username} - {self.doctor} - {self.appointment_date} {self.appointment_time}"
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
    
    def is_upcoming(self):
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(
                self.appointment_date, 
                timezone.datetime.strptime(self.appointment_time, '%H:%M').time()
            )
        )
        return appointment_datetime > timezone.now()
        
    def get_formatted_time(self):
        try:
            hour, minute = self.appointment_time.split(':')
            hour = int(hour)
            if hour == 0:
                return f"12:{minute} AM"
            elif hour < 12:
                return f"{hour}:{minute} AM"
            elif hour == 12:
                return f"12:{minute} PM"
            else:
                return f"{hour-12}:{minute} PM"
        except:
            return self.appointment_time

class InsurancePurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=100)
    coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_premium = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)

    # FIX: Corrected __str__ method
    def __str__(self):
        return f"{self.user.username} - {self.plan_name}"

# FIX: Renamed from PatientProfile to avoid conflict
class MedicalRecord(models.Model):
    patient_profile = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_records')
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    blood_group = models.CharField(max_length=5)
    allergies = models.TextField(blank=True, null=True)
    chronic_conditions = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    surgeries = models.TextField(blank=True, null=True)
    vaccination_status = models.CharField(max_length=50, choices=[('Fully Vaccinated', 'Fully Vaccinated'), ('Partially Vaccinated', 'Partially Vaccinated')])
    emergency_contact = models.CharField(max_length=15)
    last_checkup_date = models.DateField()

    # FIX: Corrected __str__ method
    def __str__(self):
        return self.name

class ConsultancyRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    
    # FIX: Corrected __str__ method
    def __str__(self):
        return f"{self.name} - {self.subject}"