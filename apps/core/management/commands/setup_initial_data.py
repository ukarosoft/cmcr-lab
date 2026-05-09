"""Setup idempotente para arrancar la app en producción.

Crea (si no existen):
- Organización CMCR
- Superadmin desde DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD env vars
- Admin de la org desde CMCR_ADMIN_USERNAME / _EMAIL / _PASSWORD env vars
- Datos demo (delegado a seed_demo --org-slug=cmcr)

Diseñado para correr en cada deploy sin causar duplicados.
"""
from __future__ import annotations

import os
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.core.models import Organization, User


class Command(BaseCommand):
    help = 'Setup inicial idempotente: crea organización CMCR, superadmin y admin del cliente.'

    def handle(self, *args, **options):
        # 1. Organización CMCR
        org, created = Organization.objects.get_or_create(
            slug='cmcr',
            defaults={
                'name': 'Centro Clínico Madre Carmen Rendiles',
                'is_active': True,
                'plan': 'pro',
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Organización creada: {org.name}'))
        else:
            self.stdout.write(f'• Organización ya existía: {org.name}')

        # 2. Superadmin (Ukarasoft) — credenciales desde env
        su_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'ukaroadmin')
        su_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@ukarasoft.com')
        su_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if su_password and not User.objects.filter(username=su_username).exists():
            User.objects.create_user(
                username=su_username,
                email=su_email,
                password=su_password,
                role='superadmin',
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Superadmin creado: {su_username}'))
        elif User.objects.filter(username=su_username).exists():
            self.stdout.write(f'• Superadmin ya existía: {su_username}')
        else:
            self.stdout.write(self.style.WARNING(
                '⚠ DJANGO_SUPERUSER_PASSWORD no configurado — superadmin no creado'
            ))

        # 3. Admin del cliente — credenciales desde env
        admin_username = os.environ.get('CMCR_ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('CMCR_ADMIN_EMAIL', 'admin@cmcr.local')
        admin_password = os.environ.get('CMCR_ADMIN_PASSWORD', 'admin123')

        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                organization=org,
                role='admin',
                first_name='Administrador',
                last_name='CMCR',
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Admin CMCR creado: {admin_username}'))
        else:
            self.stdout.write(f'• Admin ya existía: {admin_username}')

        # 4. Datos demo (idempotente — seed_demo usa get_or_create)
        if os.environ.get('LOAD_DEMO_DATA', 'true').lower() in ('1', 'true', 'yes'):
            self.stdout.write('→ Cargando datos demo...')
            try:
                call_command('seed_demo', org_slug='cmcr')
                self.stdout.write(self.style.SUCCESS('✓ Datos demo cargados'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠ seed_demo falló (no crítico): {e}'))

        self.stdout.write(self.style.SUCCESS('\n✓ Setup inicial completado'))
