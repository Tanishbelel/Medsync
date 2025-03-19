from django.core.management.base import BaseCommand
from main.models import Doctor

class Command(BaseCommand):
    help = 'Creates sample doctors for development purposes'

    def handle(self, *args, **kwargs):
        # Sample doctor data with minimal fields
        doctors = [
            {"first_name": "Sarah", "last_name": "Johnson", "is_active": True},
            {"first_name": "Michael", "last_name": "Chen", "is_active": True},
            {"first_name": "Rebecca", "last_name": "Martinez", "is_active": True},
            {"first_name": "David", "last_name": "Wilson", "is_active": True},
            {"first_name": "Amara", "last_name": "Okafor", "is_active": True}
        ]
        
        created_count = 0
        for doctor_data in doctors:
            # Get or create to prevent duplicates
            _, created = Doctor.objects.get_or_create(
                first_name=doctor_data['first_name'],
                last_name=doctor_data['last_name'],
                defaults=doctor_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created doctor: {doctor_data['first_name']} {doctor_data['last_name']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} doctors')
        )