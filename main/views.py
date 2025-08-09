from django.shortcuts import render, redirect,get_object_or_404
import time
from .models import *
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from datetime import timedelta, date
from django.db.models import Q
from django.db.models import Count
from django.http import JsonResponse
from decimal import Decimal
from .models import CartItem
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
import re
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from .forms import *


from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from datetime import datetime, timedelta
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.db import transaction 



# Define patterns for queries you want to handle specially
DATE_PATTERNS = [
    r"what('s| is)? (the )?date",
    r"what day is (it|today)",
    r"today'?s date",
    r"current date"
]

TIME_PATTERNS = [
    r"what('s| is)? (the )?time",
    r"current time"
]


def home(request):
    products = [
        {"name": "Physics Labbook", "price": Decimal('50.00')},
        {"name": "Chemistry Labbook", "price": Decimal('50.00')},
        {"name": "Maths Labbook", "price": Decimal('50.00')},
      
    ]
    
    return render(request, 'index.html', {'products': products})

def login_page(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('main')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html')

def register_page(request):
    if request.method == "POST":
        # Get data from the form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        referral_code = request.POST.get('referral_code')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('/register/')

        referrer_user = None 
        
        # This block checks the referral code
        if referral_code:
            try:
                # -----------------------------------------------------------
                # >> THE FIX IS ON THIS LINE <<
                # It now correctly queries the 'Student' model, not 'User'.
                referrer_profile = Student.objects.get(referral_code=referral_code)
                # -----------------------------------------------------------
                
                referrer_user = referrer_profile.user
                messages.info(request, f"Referral from {referrer_user.username} applied!")

            except Student.DoesNotExist:
                messages.error(request, "The referral code is invalid.")
                return redirect('/register/')
        
        # Create the new user
        new_user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create the 'Student' profile for the new user
        new_student_profile = Student.objects.create(
            user=new_user,
            student_id=f"STUDENT_{new_user.id}", # Example ID
            referred_by=referrer_user # Assign the referrer if one was found
        )
        
        # Create the 'PatientProfile' for the new user
        PatientProfile.objects.create(user=new_user)
        
        # Optional: Give points to the referrer
        if referrer_user:
            try:
                referrer_student_profile = Student.objects.get(user=referrer_user)
                referrer_student_profile.points += 100
                referrer_student_profile.save()
            except Student.DoesNotExist:
                pass # Should not happen if code was valid, but good practice

        messages.success(request, f"Welcome, {username}! Your account has been created.")
        return redirect('/login/')

    return render(request, 'register.html')

def logout_page(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required(login_url = '/login/')
def main(request):
    events = Event.objects.filter(status='published').order_by('-created_at')
    return render(request, 'main.html', {'events': events})
@login_required(login_url = '/login/')
def product_list(request):
    return render(request, 'prods.html')
@login_required
def store(request):
    products = [
        {"name": "Physics Labbook", "price": Decimal('50.00')},
        {"name": "Chemistry Labbook", "price": Decimal('50.00')},
        {"name": "Maths Labbook", "price": Decimal('50.00')},
    ]
    return render(request, 'store.html', {'products': products})

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        price = request.POST.get('price')
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product_name=product_name,
            defaults={'price': price}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
            
        return JsonResponse({'status': 'success', 'cart_count': get_cart_count(request.user)})
    return JsonResponse({'status': 'error'})

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.get_total() for item in cart_items)
    tax = subtotal * Decimal('0.08')  # 8% tax
    total = subtotal + tax
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    }
    return render(request, 'cart.html', context)

@login_required
def update_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            if action == 'increase':
                cart_item.quantity += 1
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
            cart_item.save()
            
            return JsonResponse({
                'status': 'success',
                'quantity': cart_item.quantity,
                'total': float(cart_item.get_total()),
                'cart_total': float(get_cart_total(request.user))
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        try:
            cart_item = CartItem.objects.get(id=item_id, user=request.user)
            cart_item.delete()
            return JsonResponse({'status': 'success'})
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

def get_cart_count(user):
    return CartItem.objects.filter(user=user).count()

def get_cart_total(user):
    cart_items = CartItem.objects.filter(user=user)
    return sum(item.get_total() for item in cart_items)



def is_admin(user):
    return user.is_staff

@never_cache
def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials')
            
    return render(request, 'admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')

def create_admin_account(request):
    if request.method == 'POST':
        # Fetching form data
        fullname = request.POST.get('fullname', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        admin_code = request.POST.get('admin_code', '').strip()

        # Basic validation
        if not all([fullname, username, password, confirm_password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'admin_register.html')

        # Username validation
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            messages.error(request, 'Username must be 3-20 characters long and contain only letters, numbers, and underscores.')
            return render(request, 'admin_register.html')

        # Password validation
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'admin_register.html')

        if not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
            messages.error(request, 'Password must contain at least one uppercase letter, one lowercase letter, and one number.')
            return render(request, 'admin_register.html')

        # Password confirmation validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'admin_register.html')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'admin_register.html')

        try:
            # Creating the user with admin privileges
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=fullname,
                is_staff=True,
                is_superuser=True  # Grant full admin privileges
            )

            # Create additional admin profile if needed
            # AdminProfile.objects.create(user=user, ...)

            messages.success(request, 'Admin account created successfully.')
            return redirect('admin_login')

        except ValidationError as e:
            messages.error(request, f"Error: {', '.join(e.messages)}")
        except Exception as e:
            messages.error(request, 'An error occurred while creating the account. Please try again.')
            
    return render(request, 'admin_register.html')


def verify_admin_code(code):
    """
    Verify the admin registration code.
    Replace this with your actual verification logic.
    """

@login_required
@require_POST
def cancel_order(request):
    try:
        student = Student.objects.get(user=request.user)
        order = Order.objects.get(
            student=student,
            status='Processing'
        )
        
        order.status = 'Cancelled'
        order.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Order cancelled successfully'
        })
        
    except (Order.DoesNotExist, Student.DoesNotExist):
        return JsonResponse({
            'status': 'error',
            'message': 'Order not found or cannot be cancelled'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while cancelling the order'
        }, status=500)
    
def is_admin(user):
    return user.is_staff and user.is_authenticated


def create_order(request):
    if request.method == 'POST':
        try:
            # Get cart items for current user
            cart_items = CartItem.objects.filter(user=request.user)
            
            # Calculate totals
            subtotal = sum(item.get_total() for item in cart_items)
            platform_fee = subtotal * 0.02
            total = subtotal + platform_fee
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                subtotal=subtotal,
                platform_fee=platform_fee,
                total_amount=total,
                status='Processing'
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_name=cart_item.product_name,
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    total_price=cart_item.get_total()
                )
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def order_list(request):
    appointments = Appointment.objects.filter(patient=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'orders.html', {'orders': orders,'appointments': appointments})
@login_required 
def create_order(request):
    if request.method == 'POST':
        try:
            cart_items = CartItem.objects.filter(user=request.user)
            
            # Check if cart is empty
            if not cart_items.exists():
                return JsonResponse({'status': 'error', 'message': 'Cart is empty'})
            
            # Calculate totals
            subtotal = sum(item.get_total() for item in cart_items)
            platform_fee = subtotal * Decimal('0.02')  
            total_amount = subtotal + platform_fee
            
            # Create order with a unique order number
            order = Order.objects.create(
                user=request.user,
                subtotal=subtotal,
                platform_fee=platform_fee,
                total_amount=total_amount,
                status='PENDING',
                order_number=f"ORD-{int(time.time())}"  # Add a unique order number
            )
            
            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product_name=cart_item.product_name,
                    price=cart_item.price,
                    quantity=cart_item.quantity
                )
            
            # Clear cart
            cart_items.delete()
            
            # Return success with redirect URL
            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('orders')  # Add the URL name for your orders page
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
@login_required
def orders(request):
    try:
        # Print debugging information
        print(f"Current user: {request.user.username}")
        
        # Get all orders for the current user
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        print(f"Number of orders found: {orders.count()}")
        
        # Get all appointments for the current user
        appointments = Appointment.objects.filter(patient=request.user).order_by('appointment_date', 'appointment_time')
        print(f"Number of appointments found: {appointments.count()}")
        
        # Print details of each order
        for order in orders:
            print(f"""
                Order details:
                - Order number: {order.order_number}
                - Status: {order.status}
                - Total: {order.total_amount}
                - Items: {order.items.all().count()}
            """)
        
        # Print details of each appointment
        for appointment in appointments:
            print(f"""
                Appointment details:
                - Doctor: Dr. {appointment.doctor.last_name}
                - Date: {appointment.appointment_date}
                - Time: {appointment.appointment_time}
                - Status: {appointment.status}
            """)
        
        context = {
            'appointments': appointments,
            'orders': orders,
            'debug_info': {
                'user': request.user.username,
                'order_count': orders.count(),
                'appointment_count': appointments.count(),
                'orders_list': [
                    {
                        'number': order.order_number,
                        'status': order.status,
                        'total': float(order.total_amount),
                        'items_count': order.items.all().count()
                    } for order in orders
                ],
                'appointments_list': [
                    {
                        'doctor': f"Dr. {appointment.doctor.last_name}",
                        'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                        'time': appointment.appointment_time,
                        'status': appointment.status
                    } for Appoint in Appointment
                ]
            }
        }
        
        return render(request, 'orders.html', context)
    
    except Exception as e:
        print(f"Error in orders view: {str(e)}")
        return render(request, 'orders.html', {'error': str(e)})
def is_staff(user):
    return user.is_staff

@login_required
def admin_dashboard(request):
    orders = Order.objects.all().order_by('-created_at')
    context = {
        'orders': orders,
        'total_orders': orders.count(),
    }
    return render(request, 'admin_panel.html', context)

@login_required
@user_passes_test(is_staff)
def get_order_details(request):
    order_id = request.GET.get('order_id')
    try:
        order = Order.objects.get(id=order_id)
        html = render_to_string('order_details.html', {'order': order})
        return JsonResponse({'html': html})
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

@login_required
@user_passes_test(is_staff)
def update_order_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            # Update status based on current status
            if order.status == 'pending':
                order.status = 'completed'
            elif order.status == 'completed':
                order.status = 'cancelled'
            else:
                order.status = 'pending'
            order.save()
            return JsonResponse({'status': 'success', 'new_status': order.status})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@staff_member_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'adminorder_details.html', {'order': order})

@login_required
def split_payment(request):
    from decimal import Decimal
    
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.get_total() for item in cart_items)
    tax = subtotal * Decimal('0.02')
    total = subtotal + tax
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    }
    return render(request, 'split_payment.html', context)
@login_required
def smart_navigation(request, order_id):
    # Sample data - replace with your actual data from database
    food_stalls = [
        {
            'name': 'Tasty Delights',
            'location': 'Zone A-1',
            'description': 'Traditional local cuisine with modern twists',
            'offers': ['20% off on combo meals', 'Free dessert with meals above ₹500']
        },
        {
            'name': 'Street Food Corner',
            'location': 'Zone B-2',
            'description': 'Popular street food from around the country',
            'offers': ['Buy 1 Get 1 on selected items']
        },
        # Add more food stalls...
    ]
    
    other_stalls = [
        {
            'name': 'Craft Bazaar',
            'location': 'Zone C-1',
            'description': 'Handmade crafts and local artworks',
            'offers': ['Early bird discount - 15% off before 2 PM']
        },
        {
            'name': 'Game Zone',
            'location': 'Zone D-3',
            'description': 'Interactive games and entertainment',
            'offers': ['Family package: 4 people for price of 3']
        },
        # Add more stalls...
    ]
    
    return render(request, 'smart_navigation.html', {
        'food_stalls': food_stalls,
        'other_stalls': other_stalls
    })

@login_required
def vendor_registration(request):
    try:
        # Check if user already has a vendor profile
        vendor = request.user.vendor
        messages.info(request, "You are already registered as a vendor.")
        return redirect('vendor_dashboard')
    except Vendor.DoesNotExist:
        if request.method == 'POST':
            form = VendorRegistrationForm(request.POST)
            if form.is_valid():
                vendor = form.save(commit=False)
                vendor.user = request.user
                vendor.save()
                messages.success(request, "Vendor registration successful!")
                return redirect('vendor_dashboard')
        else:
            form = VendorRegistrationForm()
        return render(request, 'vendor_registration.html', {'form': form})

@login_required
def vendor_dashboard(request):
    try:
        vendor = request.user.vendor
        events = Event.objects.filter(vendor=vendor)
        appointments = Appointment.objects.filter(patient=request.user)
        
        return render(request, 'dashboard.html', {'events': events,'appointments': appointments})
    except Vendor.DoesNotExist:
        messages.warning(request, "Please register as a vendor first.")
        return redirect('vendor_registration')

@login_required
def create_event(request):
    try:
        vendor = request.user.vendor
    except Vendor.DoesNotExist:
        messages.warning(request, "Please register as a vendor first.")
        return redirect('vendor_registration')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.vendor = vendor
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('vendor_dashboard')
    else:
        form = EventForm()
    return render(request, 'create_event.html', {'form': form})

@login_required
def create_appointment(request):
    try:
        # Assuming you have a Patient model linked to User
        patient = request.user
    except Exception:
        messages.warning(request, "Please register as a patient first.")
        return redirect('patient_registration')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            
            # Check if the selected time slot is available
            doctor = form.cleaned_data['doctor']
            date = form.cleaned_data['appointment_date']
            time = form.cleaned_data['appointment_time']
            
            if Appointment.objects.filter(doctor=doctor, appointment_date=date, 
                                          appointment_time=time).exists():
                messages.error(request, "This time slot is already booked. Please select another time.")
            else:
                appointment.save()
                messages.success(request, 'Appointment scheduled successfully!')
                return redirect('vendor_dashboard')
    else:
        form = AppointmentForm()
    
    return render(request, 'create_appointment.html', {'form': form})


@login_required
def buy_vibies(request):
    return render(request,'vibies.html')
@login_required
def select_seats(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'select_seats.html', {'event': event})

def delete_event(request, event_id):
    # Get the event or return 404
    event = get_object_or_404(Event, id=event_id)
    
    # Check if the current user is the vendor who created this event
    if request.user.vendor == event.vendor:
        # Store the name for the success message
        event_name = event.name
        event.delete()
        messages.success(request, f"'{event_name}' has been deleted successfully.")
    else:
        messages.error(request, "You don't have permission to delete this event.")
    
    # Redirect to the vendor dashboard
    return redirect('vendor_dashboard')
from .models import Doctor, Appointment, InsuranceInfo
from .forms import AppointmentForm, InsuranceInfoForm

@login_required
def book_consultation(request):
    """
    View for booking a new consultation.
    Handles both GET (display form) and POST (process form) requests.
    """
    # Get all active doctors
    doctors = Doctor.objects.filter(is_active=True).order_by('specialization', 'last_name')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        insurance_form = InsuranceInfoForm(request.POST)
        
        if form.is_valid() and insurance_form.is_valid():
            try:
                # Create appointment but don't save yet
                appointment = form.save(commit=False)
                appointment.patient = request.user
                
                # Check if the slot is still available
                existing_appointments = Appointment.objects.filter(
                    doctor=appointment.doctor,
                    appointment_date=appointment.appointment_date,
                    appointment_time=appointment.appointment_time
                )
                
                if existing_appointments.exists():
                    messages.error(request, "Sorry, that time slot has just been booked. Please select another time.")
                    return render(request, 'book_consultation.html', {
                        'form': form,
                        'insurance_form': insurance_form,
                        'doctors': doctors
                    })
                
                # Save the appointment
                appointment.save()
                
                # Save or update insurance info
                if insurance_form.has_changed():
                    insurance_info, created = InsuranceInfo.objects.update_or_create(
                        patient=request.user,
                        defaults={
                            'provider': insurance_form.cleaned_data['insurance'],
                            'policy_number': insurance_form.cleaned_data['policy_number']
                        }
                    )
                
                # Set new patient flag if checked
                if 'new_patient' in request.POST:
                    # Update user profile or associated patient profile
                    profile = request.user.profile
                    profile.is_new_patient = True
                    profile.save()
                
                messages.success(request, "Appointment booked successfully! You'll receive a confirmation email shortly.")
                return redirect('appointment_confirmation', appointment_id=appointment.id)
                
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return render(request, 'booking/book_consultation.html', {
                    'form': form,
                    'insurance_form': insurance_form,
                    'doctors': doctors
                })
        else:
            # Form validation failed
            messages.error(request, "Please correct the errors in the form.")
    else:
        # GET request - display empty form
        form = AppointmentForm()
        
        # Pre-fill insurance info if available
        try:
            insurance_info = InsuranceInfo.objects.get(patient=request.user)
            insurance_form = InsuranceInfoForm(initial={
                'insurance': insurance_info.provider,
                'policy_number': insurance_info.policy_number
            })
        except InsuranceInfo.DoesNotExist:
            insurance_form = InsuranceInfoForm()
    
    return render(request, 'consultation.html', {
        'form': form,
        'insurance_form': insurance_form,
        'doctors': doctors
    })

@login_required
def appointment_confirmation(request, appointment_id):
    """
    Display confirmation page after successful booking
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id, patient=request.user)
        return render(request, 'booking/confirmation.html', {'appointment': appointment})
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
        return redirect('dashboard')

@login_required
def get_doctor_availability(request, doctor_id):
    """
    AJAX endpoint to fetch doctor availability for a specific date
    """
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        selected_date = request.GET.get('date')
        
        if not selected_date:
            return JsonResponse({'error': 'Date is required'}, status=400)
        
        # Parse the date
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
        
        # Check if date is in the past
        if date_obj < timezone.now().date():
            return JsonResponse({'error': 'Cannot check availability for past dates'}, status=400)
        
        # Get all booked slots for this doctor on the selected date
        booked_slots = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date_obj
        ).values_list('appointment_time', flat=True)
        
        # Get doctor's available hours based on their schedule
        # This is a simplified version - in a real app, you'd check the doctor's working hours
        all_slots = [
            '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00',
            '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
        ]
        
        # Remove booked slots from available slots
        available_slots = [slot for slot in all_slots if slot not in booked_slots]
        
        return JsonResponse({
            'doctor_name': f"Dr. {doctor.first_name} {doctor.last_name}",
            'date': selected_date,
            'available_slots': available_slots
        })
        
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """
    Cancel an existing appointment
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id, patient=request.user)
        
        # Check if appointment is in the future and cancellation is allowed
        if appointment.appointment_date < timezone.now().date():
            messages.error(request, "Cannot cancel past appointments.")
            return redirect('dashboard')
            
        # Check if appointment is within 24 hours (for cancellation policy)
        appointment_datetime = datetime.combine(
            appointment.appointment_date, 
            datetime.strptime(appointment.appointment_time, '%H:%M').time()
        )
        
        if timezone.make_aware(appointment_datetime) - timezone.now() < timedelta(hours=24):
            messages.warning(request, "Appointment cancelled with late cancellation fee.")
            # Here you could add logic to apply a cancellation fee
        else:
            messages.success(request, "Appointment cancelled successfully.")
        
        # Mark as cancelled rather than deleting
        appointment.status = 'CANCELLED'
        appointment.save()
        
        return redirect('dashboard')
        
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
        return redirect('dashboard')
@login_required
def insurance_page(request):
    if request.method == "POST":
        form = InsurancePurchaseForm(request.POST)
        if form.is_valid():
            insurance = form.save(commit=False)
            insurance.user = request.user
            insurance.save()
            return redirect('insurance_success')  # Redirect after purchase
    else:
        form = InsurancePurchaseForm()
    
    return render(request, 'insurance.html', {'form': form})

def insurance_success(request):
    return render(request, 'insurance_success.html')

def ambulance(request):
    return render(request,'emerg.html')

from .forms import PatientProfileForm
def profile(request):
    if request.method == "POST":
        form = PatientProfileForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PatientProfileForm()
    
    patients = PatientProfile.objects.all()
    return render(request, 'profile.html', {'form': form, 'patients': patients})

@login_required
def cancel_appointment(request, appointment_id):
    """View to cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Security check: ensure the user owns this appointment
    if appointment.patient != request.user:
        return HttpResponseForbidden("You don't have permission to cancel this appointment")
    
    # Only allow cancellation if the appointment is upcoming and not already cancelled
    if appointment.is_upcoming() and appointment.status != 'CANCELLED':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, f"Your appointment with Dr. {appointment.doctor.last_name} on {appointment.appointment_date} has been cancelled.")
    else:
        messages.error(request, "This appointment cannot be cancelled.")
    
    # Redirect back to the dashboard or wherever the user came from
    return redirect('vendor_dashboard')  # Adjust this to your actual dashboard URL name

@login_required
def appointment_details(request, appointment_id):
    """View to display appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Security check: ensure the user owns this appointment
    if appointment.patient != request.user:
        return HttpResponseForbidden("You don't have permission to view this appointment")
    
    return render(request, 'appointment_details.html', {'appointment': appointment})

@login_required
def edit_appointment(request, appointment_id):
    """View to edit an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Security check: ensure the user owns this appointment
    if appointment.patient != request.user:
        return HttpResponseForbidden("You don't have permission to edit this appointment")
    
    if not appointment.is_upcoming() or appointment.status == 'CANCELLED':
        messages.error(request, "This appointment cannot be edited.")
        return redirect('vendor_dashboard')  # Adjust to your actual dashboard URL
    
    if request.method == 'POST':
        # Process the form data
        # This will depend on what fields you want to allow editing
        # For example:
        reason = request.POST.get('reason')
        if reason:
            appointment.reason = reason
            appointment.save()
            messages.success(request, "Appointment updated successfully.")
            return redirect('vendor_dashboard')  # Adjust to your dashboard URL
    
    # For GET requests, show the edit form
    return render(request, 'edit_appointment.html', {'appointment': appointment})

from django.shortcuts import render
import json
from django.shortcuts import render
import json


def map_view(request):
    # List of 20 medical stores in Andheri with details
    medical_stores = [
        {"name": "Apna Medical & General Stores", "lat": 19.1196, "lng": 72.8468, "address": "Andheri West, Mumbai", "timings": "9 AM - 11 PM"},
        {"name": "Get Well Medical", "lat": 19.1210, "lng": 72.8491, "address": "Andheri East, Mumbai", "timings": "24 Hours"},
        {"name": "People Chemist", "lat": 19.1185, "lng": 72.8430, "address": "Juhu, Andheri", "timings": "8 AM - 10 PM"},
        {"name": "Wellcare Pharmacy", "lat": 19.1250, "lng": 72.8475, "address": "Andheri West", "timings": "10 AM - 9 PM"},
        {"name": "Lifeline Medicals", "lat": 19.1225, "lng": 72.8422, "address": "Andheri East", "timings": "24 Hours"},
        {"name": "MedPlus Pharmacy", "lat": 19.1170, "lng": 72.8501, "address": "Andheri East", "timings": "7 AM - 11 PM"},
        {"name": "Care & Cure Pharmacy", "lat": 19.1208, "lng": 72.8415, "address": "Lokhandwala, Andheri", "timings": "10 AM - 10 PM"},
        {"name": "Health Point Medical", "lat": 19.1267, "lng": 72.8449, "address": "Four Bungalows, Andheri", "timings": "9 AM - 11 PM"},
        {"name": "Apollo Pharmacy", "lat": 19.1156, "lng": 72.8463, "address": "Andheri West", "timings": "24 Hours"},
        {"name": "Wellness Chemist", "lat": 19.1182, "lng": 72.8490, "address": "Seven Bungalows, Andheri", "timings": "9 AM - 10 PM"},
        {"name": "Prime Medicals", "lat": 19.1244, "lng": 72.8502, "address": "DN Nagar, Andheri", "timings": "8 AM - 11 PM"},
        {"name": "Reliable Pharmacy", "lat": 19.1212, "lng": 72.8535, "address": "Mahakali Caves, Andheri", "timings": "7 AM - 12 AM"},
        {"name": "HealthFirst Chemist", "lat": 19.1180, "lng": 72.8395, "address": "Versova, Andheri", "timings": "9 AM - 11 PM"},
        {"name": "City Medicos", "lat": 19.1262, "lng": 72.8405, "address": "Jogeshwari-Vikhroli Link Rd", "timings": "10 AM - 10 PM"},
        {"name": "QuickMeds Pharmacy", "lat": 19.1135, "lng": 72.8440, "address": "Andheri West", "timings": "24 Hours"},
        {"name": "MediTrust Pharmacy", "lat": 19.1203, "lng": 72.8378, "address": "Yari Road, Andheri", "timings": "8 AM - 11 PM"},
        {"name": "Apex Medical Store", "lat": 19.1169, "lng": 72.8517, "address": "Marol, Andheri", "timings": "10 AM - 9 PM"},
        {"name": "LifeCare Pharmacy", "lat": 19.1237, "lng": 72.8529, "address": "JB Nagar, Andheri", "timings": "24 Hours"},
        {"name": "Om Sai Medicals", "lat": 19.1174, "lng": 72.8466, "address": "Andheri East", "timings": "8 AM - 10 PM"},
        {"name": "Sanford Chemist", "lat": 19.1159, "lng": 72.8403, "address": "Versova, Andheri", "timings": "9 AM - 11 PM"}
    ]

    return render(request, 'map.html', {'medical_stores': json.dumps(medical_stores)})


@login_required
def consultancy(request):
    if request.method == 'POST':
        form = ConsultancyRequestForm(request.POST)
        if form.is_valid():
            # Process the form data
            # You can save to database or send email etc.
            
            # Example: Save to database
            # consultancy_request = ConsultancyRequest(
            #     user=request.user,
            #     name=form.cleaned_data['name'],
            #     email=form.cleaned_data['email'],
            #     phone=form.cleaned_data['phone'],
            #     subject=form.cleaned_data['subject'],
            #     message=form.cleaned_data['message'],
            #     preferred_date=form.cleaned_data['preferred_date'],
            #     preferred_time=form.cleaned_data['preferred_time']
            # )
            # consultancy_request.save()
            
            messages.success(request, 'Your consultancy request has been submitted successfully! We will contact you shortly.')
            return redirect('request_consultancy')
    else:
        # Pre-fill name and email if user is logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': f"{request.user.first_name} {request.user.last_name}".strip(),
                'email': request.user.email
            }
        form = ConsultancyRequestForm(initial=initial_data)
    
    return render(request, 'consultancy.html', {'form': form})

@login_required
def meditate(request):
    return render(request,'meditate.html')

@login_required
def clock(request):
    return render(request,'medClock.html')

@login_required
def assessment(request):
    return render(request,'assessment.html')

@login_required
def subscription(request):
    return render(request,'subscription.html')

@login_required
def mannai(request):
    return render(request,'newchat.html')

