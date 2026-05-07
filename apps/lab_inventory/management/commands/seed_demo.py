from __future__ import annotations
from django.core.management.base import BaseCommand
from apps.core.models import Organization
from apps.lab_inventory.models import (
    Category, UnitOfMeasure, Supply, Supplier,
    Reagent, ReagentItem, StockMovement,
)


class Command(BaseCommand):
    help = 'Carga datos demo completos: insumos, reactivos con recetas y movimientos de stock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-slug',
            type=str,
            required=True,
            help='Slug de la organización donde cargar los datos demo',
        )

    def handle(self, *args, **options):
        try:
            org = Organization.objects.get(slug=options['org_slug'])
        except Organization.DoesNotExist:
            self.stderr.write(
                f'Organización con slug "{options["org_slug"]}" no existe. '
                f'Slugs disponibles: {", ".join(Organization.objects.values_list("slug", flat=True))}'
            )
            return

        # ── Obtener o crear categorías ──
        cat_reactive, _ = Category.objects.get_or_create(
            organization=org, name='Reactivo base',
            defaults={'description': 'Sustancias químicas base para preparar reactivos'},
        )
        cat_solvent, _ = Category.objects.get_or_create(
            organization=org, name='Solvente',
            defaults={'description': 'Solventes y diluyentes para laboratorio'},
        )
        cat_buffer, _ = Category.objects.get_or_create(
            organization=org, name='Buffer',
            defaults={'description': 'Soluciones buffer y tampones de pH'},
        )
        cat_control, _ = Category.objects.get_or_create(
            organization=org, name='Control',
            defaults={'description': 'Controles de calidad internos'},
        )

        # ── Obtener o crear unidades ──
        g, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='g', defaults={'name': 'Gramo'})
        mg, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='mg', defaults={'name': 'Miligramo'})
        ml, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='mL', defaults={'name': 'Mililitro'})
        l, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='L', defaults={'name': 'Litro'})
        ud, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='ud', defaults={'name': 'Unidad'})
        fco, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='fco', defaults={'name': 'Frasco'})
        kit, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='kit', defaults={'name': 'Kit'})
        ul, _ = UnitOfMeasure.objects.get_or_create(organization=org, abbreviation='µL', defaults={'name': 'Microlitro'})

        # ── Obtener proveedor ──
        supplier = Supplier.objects.for_tenant(org).first()
        if not supplier:
            supplier = Supplier.objects.create(
                organization=org, name='Reactivos y Suministros C.A.',
                rif='J-12345678-9', contact_name='Carlos Mendoza',
            )

        # ── Crear insumos demo ──
        supplies_data = [
            {'code': 'INS-001', 'name': 'Glucosa anhidra', 'category': cat_reactive, 'unit': g, 'stock_min': 100, 'stock_max': 2000},
            {'code': 'INS-002', 'name': 'Cloruro de sodio', 'category': cat_reactive, 'unit': g, 'stock_min': 200, 'stock_max': 5000},
            {'code': 'INS-003', 'name': 'Ácido úrico estándar', 'category': cat_control, 'unit': mg, 'stock_min': 50, 'stock_max': 500},
            {'code': 'INS-004', 'name': 'Creatinina base', 'category': cat_reactive, 'unit': g, 'stock_min': 25, 'stock_max': 500},
            {'code': 'INS-005', 'name': 'Fosfato monobásico', 'category': cat_buffer, 'unit': g, 'stock_min': 100, 'stock_max': 1000},
            {'code': 'INS-006', 'name': 'Fosfato dibásico', 'category': cat_buffer, 'unit': g, 'stock_min': 100, 'stock_max': 1000},
            {'code': 'INS-007', 'name': 'Solución salina 0.9%', 'category': cat_solvent, 'unit': ml, 'stock_min': 500, 'stock_max': 5000},
            {'code': 'INS-008', 'name': 'Agua destilada estéril', 'category': cat_solvent, 'unit': ml, 'stock_min': 1000, 'stock_max': 10000},
            {'code': 'INS-009', 'name': '4-Aminoantipirina', 'category': cat_reactive, 'unit': g, 'stock_min': 10, 'stock_max': 200},
            {'code': 'INS-010', 'name': 'Peroxidasa (HRP)', 'category': cat_reactive, 'unit': mg, 'stock_min': 100, 'stock_max': 2000},
            {'code': 'INS-011', 'name': 'Colesterol estándar 200 mg/dL', 'category': cat_control, 'unit': ml, 'stock_min': 10, 'stock_max': 100},
            {'code': 'INS-012', 'name': 'Triglicéridos estándar', 'category': cat_control, 'unit': ml, 'stock_min': 10, 'stock_max': 100},
        ]

        supplies = {}
        for data in supplies_data:
            code = data.pop('code')
            cat = data.pop('category')
            unit = data.pop('unit')
            s, created = Supply.objects.get_or_create(
                organization=org, code=code,
                defaults={**data, 'category': cat, 'unit': unit},
            )
            supplies[code] = s
            if created:
                self.stdout.write(f'  ✅ Insumo: {s.name}')

        # ── Registrar entradas de stock ──
        stock_entries = [
            ('INS-001', 1000, 'L-2026-001'),
            ('INS-002', 2000, 'L-2026-001'),
            ('INS-003', 200, 'L-2026-002'),
            ('INS-004', 100, 'L-2026-002'),
            ('INS-005', 500, 'L-2026-003'),
            ('INS-006', 500, 'L-2026-003'),
            ('INS-007', 2000, 'L-2026-004'),
            ('INS-008', 5000, 'L-2026-004'),
            ('INS-009', 50, 'L-2026-005'),
            ('INS-010', 500, 'L-2026-005'),
            ('INS-011', 30, 'L-2026-006'),
            ('INS-012', 30, 'L-2026-006'),
        ]
        for code, qty, batch in stock_entries:
            if code in supplies:
                StockMovement.objects.create(
                    organization=org,
                    supply=supplies[code],
                    movement_type='entry',
                    quantity=qty,
                    batch_number=batch,
                    supplier=supplier,
                    reason=f'Compra inicial — lote {batch}',
                )

        # ── Crear reactivo demo: Glucosa Enzimática ──
        reagent, created = Reagent.objects.get_or_create(
            organization=org, name='Glucosa Enzimática (GOD-PAP)',
            defaults={
                'code': 'REA-001',
                'description': 'Reactivo para determinación cuantitativa de glucosa en suero o plasma por método enzimático colorimétrico GOD-PAP.',
                'preparation_instructions': '1. Reconstituir el frasco de enzimas con 100 mL de buffer.\n2. Mezclar suavemente hasta disolución completa.\n3. Estabilizar 30 min a temperatura ambiente antes de usar.\n4. Almacenar entre 2-8°C. Estable por 30 días.',
                'yield_quantity': 100,
                'yield_unit': ml,
                'tracks_batch': True,
            },
        )
        if created:
            self.stdout.write(f'  ✅ Reactivo: {reagent.name}')
            # Agregar ítems a la receta
            items = [
                (supplies['INS-007'], 80, ml, 'Buffer fosfato 0.1M pH 7.0'),
                (supplies['INS-009'], 0.5, g, '4-Aminoantipirina'),
                (supplies['INS-010'], 10, mg, 'Peroxidasa >1000 U/mg'),
                (supplies['INS-005'], 5, g, 'Fosfato monobásico'),
                (supplies['INS-011'], 1, ml, 'Estándar de calibración'),
            ]
            for supply, qty, unit, notes in items:
                ReagentItem.objects.create(
                    organization=org, reagent=reagent, supply=supply,
                    quantity=qty, unit=unit, notes=notes,
                )
            self.stdout.write(f'     ↳ {reagent.items.count()} ítems en la receta')

        # ── Crear reactivo demo: Creatinina Jaffé ──
        reagent2, created = Reagent.objects.get_or_create(
            organization=org, name='Creatinina (Método Jaffé)',
            defaults={
                'code': 'REA-002',
                'description': 'Reactivo para determinación cuantitativa de creatinina en suero u orina por método de Jaffé cinético.',
                'preparation_instructions': '1. Mezclar partes iguales de Reactivo A (ácido pícrico) y Reactivo B (buffer alcalino).\n2. Preparar fresco cada día de uso.\n3. Proteger de la luz.',
                'yield_quantity': 200,
                'yield_unit': ml,
                'tracks_batch': True,
            },
        )
        if created:
            self.stdout.write(f'  ✅ Reactivo: {reagent2.name}')
            items2 = [
                (supplies['INS-004'], 2, g, 'Creatinina base anhidra'),
                (supplies['INS-005'], 10, g, 'Buffer fosfato'),
                (supplies['INS-006'], 10, g, 'Buffer fosfato dibásico'),
                (supplies['INS-008'], 180, ml, 'Agua destilada'),
            ]
            for supply, qty, unit, notes in items2:
                ReagentItem.objects.create(
                    reagent=reagent2, supply=supply,
                    quantity=qty, unit=unit, notes=notes,
                )
            self.stdout.write(f'     ↳ {reagent2.items.count()} ítems en la receta')

        self.stdout.write(self.style.SUCCESS(
            f'\nDatos demo completos cargados para: {org.name}\n'
            f'  {Supply.objects.for_tenant(org).count()} insumos con stock\n'
            f'  {Reagent.objects.for_tenant(org).count()} reactivos con recetas\n'
            f'  {StockMovement.objects.for_tenant(org).count()} movimientos de stock\n'
        ))
