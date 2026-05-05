from __future__ import annotations
from django.core.management.base import BaseCommand
from apps.core.models import Organization
from apps.lab_inventory.models import Category, UnitOfMeasure, Supplier


class Command(BaseCommand):
    help = 'Carga datos demo: categorías, unidades de medida y proveedores para laboratorio clínico'

    def handle(self, *args, **options):
        org = Organization.objects.first()
        if not org:
            self.stderr.write('No hay organizaciones. Crea una primero.')
            return

        # ── Categorías de insumos para laboratorio clínico ──
        categories = [
            ('Reactivo base', 'Sustancias químicas base para preparar reactivos'),
            ('Solvente', 'Solventes y diluyentes para laboratorio'),
            ('Buffer', 'Soluciones buffer y tampones de pH'),
            ('Enzima', 'Enzimas para análisis clínicos'),
            ('Anticuerpo', 'Anticuerpos monoclonales y policlonales'),
            ('Calibrador', 'Calibradores y estándares de referencia'),
            ('Control', 'Controles de calidad internos'),
            ('Colorante', 'Colorantes y tinciones para hematología'),
            ('Medio de cultivo', 'Medios de cultivo para microbiología'),
            ('Material fungible', 'Tubos, puntas, guantes y material desechable'),
        ]
        for name, desc in categories:
            obj, created = Category.objects.get_or_create(
                organization=org, name=name,
                defaults={'description': desc},
            )
            if created:
                self.stdout.write(f'  ✅ Categoría: {name}')

        # ── Unidades de medida para laboratorio ──
        uoms = [
            ('Kilogramo', 'kg'),
            ('Gramo', 'g'),
            ('Miligramo', 'mg'),
            ('Microgramo', 'µg'),
            ('Litro', 'L'),
            ('Mililitro', 'mL'),
            ('Microlitro', 'µL'),
            ('Unidad', 'ud'),
            ('Frasco', 'fco'),
            ('Caja', 'caja'),
            ('Kit', 'kit'),
            ('Tableta', 'tab'),
        ]
        for name, abbr in uoms:
            obj, created = UnitOfMeasure.objects.get_or_create(
                organization=org, abbreviation=abbr,
                defaults={'name': name},
            )
            if created:
                self.stdout.write(f'  ✅ Unidad: {name} ({abbr})')

        # ── Proveedor demo ──
        suppliers = [
            {
                'name': 'Reactivos y Suministros C.A.',
                'rif': 'J-12345678-9',
                'contact_name': 'Carlos Mendoza',
                'phone': '+58 414-5550101',
                'email': 'ventas@reactivosca.com',
                'address': 'Av. Bolívar, Centro Comercial Las Américas, Piso 2, Barquisimeto',
            },
            {
                'name': 'LabSupply Internacional',
                'rif': 'J-98765432-1',
                'contact_name': 'María González',
                'phone': '+58 412-5550202',
                'email': 'info@labsupply.com',
                'address': 'Calle 23, Edif. Torre Médica, Oficina 5-A, Valencia',
            },
        ]
        for data in suppliers:
            obj, created = Supplier.objects.get_or_create(
                organization=org, name=data['name'],
                defaults=data,
            )
            if created:
                self.stdout.write(f'  ✅ Proveedor: {data["name"]}')

        self.stdout.write(self.style.SUCCESS(
            '\nDatos demo cargados exitosamente para la organización: ' + org.name
        ))
