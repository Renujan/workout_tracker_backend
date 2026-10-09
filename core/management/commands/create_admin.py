"""
Quick superuser creation for CI / fresh deploys.
Usage: python manage.py create_admin
Creates: admin / admin1234 (change immediately in production!)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a default superuser (admin / admin1234) if one does not exist.'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Superuser already exists — skipping.')
            return
        user = User.objects.create_superuser(
            username='admin',
            email='admin@progressx.app',
            password='admin1234',
        )
        self.stdout.write(self.style.SUCCESS(
            f'Superuser created: {user.username} — change password immediately!'
        ))
