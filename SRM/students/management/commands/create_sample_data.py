from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Program, Subject
from students.models import Student
from teachers.models import Teacher

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample data for testing'
    
    def handle(self, *args, **kwargs):
        # Create admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'first_name': 'System',
                'last_name': 'Admin'
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Admin created'))
        
        # Create programs
        programs = ['MSc IT', 'MBA', 'MCA']
        for prog_name in programs:
            Program.objects.get_or_create(
                name=prog_name,
                defaults={
                    'duration_years': 2,
                    'total_semesters': 4
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully'))