import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import Organization, User
from apps.lab_inventory.models import (
    Category,
    UnitOfMeasure,
    Supplier,
    Supply,
    Reagent,
    ReagentItem,
    ProductionOrder,
    StockMovement,
)

pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════
# Category
# ═══════════════════════════════════════════════════════════════════

class TestCategory:
    def test_creation(self, org_a):
        cat = Category.objects.create(
            organization=org_a, name='Solventes', description='Solventes orgánicos'
        )
        assert cat.pk is not None
        assert cat.name == 'Solventes'
        assert cat.description == 'Solventes orgánicos'
        assert cat.organization == org_a

    def test_unique_per_tenant(self, org_a):
        Category.objects.create(organization=org_a, name='Buffers')
        with pytest.raises(IntegrityError):
            Category.objects.create(organization=org_a, name='Buffers')

    def test_same_name_different_org(self, org_a, org_b):
        Category.objects.create(organization=org_a, name='Estándares')
        cat_b = Category.objects.create(organization=org_b, name='Estándares')
        assert cat_b.pk is not None

    def test_organization_relation(self, category, org_a):
        assert category.organization == org_a
        assert org_a.category_set.count() == 1
        assert org_a.category_set.first() == category

    def test_str(self, category):
        assert str(category) == 'Reactivos Base'


# ═══════════════════════════════════════════════════════════════════
# UnitOfMeasure
# ═══════════════════════════════════════════════════════════════════

class TestUnitOfMeasure:
    def test_creation(self, org_a):
        uom = UnitOfMeasure.objects.create(
            organization=org_a, name='Litro', abbreviation='L'
        )
        assert uom.pk is not None

    def test_abbreviation_unique_per_tenant(self, org_a):
        UnitOfMeasure.objects.create(
            organization=org_a, name='Kilogramo', abbreviation='kg'
        )
        with pytest.raises(IntegrityError):
            UnitOfMeasure.objects.create(
                organization=org_a, name='Kilo Alternate', abbreviation='kg'
            )

    def test_str(self, uom_kg):
        assert str(uom_kg) == 'Kilogramo (kg)'


# ═══════════════════════════════════════════════════════════════════
# Supplier
# ═══════════════════════════════════════════════════════════════════

class TestSupplier:
    def test_creation(self, supplier, org_a):
        assert supplier.pk is not None
        assert supplier.name == 'Químicos del Sur'
        assert supplier.rif == 'J-12345678-9'
        assert supplier.is_active is True
        assert supplier.organization == org_a

    def test_str(self, supplier):
        assert str(supplier) == 'Químicos del Sur'

    def test_inactive_supplier(self, org_a):
        s = Supplier.objects.create(organization=org_a, name='Inactivo S.A.', is_active=False)
        assert s.is_active is False


# ═══════════════════════════════════════════════════════════════════
# Supply
# ═══════════════════════════════════════════════════════════════════

class TestSupply:
    def test_creation(self, supply, org_a, category, uom_kg):
        assert supply.pk is not None
        assert supply.code == 'INS-001'
        assert supply.name == 'Cloruro de Sodio'
        assert supply.category == category
        assert supply.unit == uom_kg
        assert supply.stock_min == 10
        assert supply.stock_max == 50
        assert supply.organization == org_a

    def test_str_with_code(self, supply):
        assert str(supply) == 'INS-001 — Cloruro de Sodio'

    def test_str_without_code(self, org_a, category, uom_kg):
        s = Supply.objects.create(
            organization=org_a, name='Agua Destilada', category=category, unit=uom_kg
        )
        assert str(s) == 'Agua Destilada'

    def test_current_stock_no_movements(self, supply):
        assert supply.current_stock == Decimal('0')

    def test_current_stock_sums_movements(self, supply, org_a, admin_user):
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('100'),
            created_by=admin_user,
        )
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='exit', quantity=Decimal('30'),
            created_by=admin_user,
        )
        assert supply.current_stock == Decimal('70')

    def test_current_stock_ignores_other_org(self, supply, org_a, org_b, admin_user):
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('100'),
            created_by=admin_user,
        )
        # movimiento en otra organización para el mismo supply_id,
        # pero la FK supply no restringe org — dependería de for_tenant en el filtro
        StockMovement.objects.create(
            organization=org_b, supply=supply,
            movement_type='entry', quantity=Decimal('999'),
            created_by=admin_user,
        )
        assert supply.current_stock == Decimal('100')

    def test_stock_status_low(self, supply, org_a, admin_user):
        # stock_min=10, 5 <= 10 → low
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('5'),
            created_by=admin_user,
        )
        assert supply.stock_status == 'low'

    def test_stock_status_low_exact_boundary(self, supply, org_a, admin_user):
        # exactamente en stock_min → low
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('10'),
            created_by=admin_user,
        )
        assert supply.stock_status == 'low'

    def test_stock_status_ok(self, supply, org_a, admin_user):
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('20'),
            created_by=admin_user,
        )
        assert supply.stock_status == 'ok'

    def test_stock_status_high(self, supply, org_a, admin_user):
        # stock_max=50, 50 >= 50 → high
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('50'),
            created_by=admin_user,
        )
        assert supply.stock_status == 'high'

    def test_stock_status_high_above_max(self, supply, org_a, admin_user):
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('80'),
            created_by=admin_user,
        )
        assert supply.stock_status == 'high'

    def test_stock_status_max_zero_never_high(self, org_a, category, uom_kg, admin_user):
        s = Supply.objects.create(
            organization=org_a, name='Sin Max', category=category,
            unit=uom_kg, stock_min=0, stock_max=0,
        )
        StockMovement.objects.create(
            organization=org_a, supply=s,
            movement_type='entry', quantity=Decimal('100'),
            created_by=admin_user,
        )
        assert s.stock_status == 'ok'

    def test_soft_delete_hides_from_for_tenant(self, supply, org_a, admin_user):
        assert Supply.objects.for_tenant(org_a).filter(pk=supply.pk).exists()
        supply.soft_delete(user=admin_user)
        assert supply.is_deleted is True
        assert supply.deleted_by == admin_user
        assert Supply.objects.for_tenant(org_a).filter(pk=supply.pk).exists() is False

    def test_soft_delete_preserves_in_all_objects(self, supply, org_a, admin_user):
        pk = supply.pk
        supply.soft_delete(user=admin_user)
        exists = Supply.all_objects.filter(
            organization=org_a, pk=pk, is_deleted=True
        ).exists()
        assert exists is True

    def test_restore(self, supply, org_a, admin_user):
        supply.soft_delete(user=admin_user)
        supply.restore()
        assert supply.is_deleted is False
        assert supply.deleted_at is None
        assert supply.deleted_by is None
        assert Supply.objects.for_tenant(org_a).filter(pk=supply.pk).exists()

    def test_code_unique_per_tenant(self, org_a, category, uom_kg):
        Supply.objects.create(
            organization=org_a, code='UNIQUE-01', name='Insumo A',
            category=category, unit=uom_kg,
        )
        with pytest.raises(IntegrityError):
            Supply.objects.create(
                organization=org_a, code='UNIQUE-01', name='Insumo B',
                category=category, unit=uom_kg,
            )

    def test_code_same_different_org(self, org_a, org_b, category, uom_kg):
        cat_b = Category.objects.create(organization=org_b, name='Reactivos')
        uom_kg_b = UnitOfMeasure.objects.create(
            organization=org_b, name='Kilogramo', abbreviation='kg'
        )
        Supply.objects.create(
            organization=org_a, code='SHARED', name='Insumo A',
            category=category, unit=uom_kg,
        )
        s_b = Supply.objects.create(
            organization=org_b, code='SHARED', name='Insumo B',
            category=cat_b, unit=uom_kg_b,
        )
        assert s_b.pk is not None

    def test_category_relation(self, supply, category):
        assert supply.category == category
        assert category.supplies.first() == supply

    def test_unit_relation(self, supply, uom_kg):
        assert supply.unit == uom_kg
        assert uom_kg.supplies.first() == supply


# ═══════════════════════════════════════════════════════════════════
# StockMovement
# ═══════════════════════════════════════════════════════════════════

class TestStockMovement:
    def test_creation_entry(self, supply, org_a, admin_user):
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('50'),
            created_by=admin_user,
        )
        assert sm.pk is not None
        assert sm.movement_type == 'entry'
        assert sm.quantity == Decimal('50')

    def test_entry_makes_quantity_positive(self, supply, org_a, admin_user):
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('-50'),
            created_by=admin_user,
        )
        assert sm.quantity == Decimal('50')

    def test_exit_makes_quantity_negative(self, supply, org_a, admin_user):
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='exit', quantity=Decimal('30'),
            created_by=admin_user,
        )
        assert sm.quantity == Decimal('-30')

    def test_exit_negative_stays_negative(self, supply, org_a, admin_user):
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='exit', quantity=Decimal('-30'),
            created_by=admin_user,
        )
        assert sm.quantity == Decimal('-30')

    def test_adjustment_preserves_sign(self, supply, org_a, admin_user):
        sm_pos = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='adjustment', quantity=Decimal('15'),
            created_by=admin_user,
        )
        assert sm_pos.quantity == Decimal('15')

        sm_neg = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='adjustment', quantity=Decimal('-10'),
            created_by=admin_user,
        )
        assert sm_neg.quantity == Decimal('-10')

    def test_supply_relation(self, supply, org_a, admin_user):
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('10'),
            created_by=admin_user,
        )
        assert sm.supply == supply
        assert supply.movements.count() == 1

    def test_production_order_relation(self, supply, org_a, admin_user, uom_ml):
        reagent = Reagent.objects.create(
            organization=org_a, name='Reactivo X', yield_unit=uom_ml,
        )
        po = ProductionOrder.objects.create(
            organization=org_a, reagent=reagent,
            batch_number='LOTE-001', quantity=Decimal('10'),
            created_by=admin_user,
        )
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='exit', quantity=Decimal('5'),
            production_order=po, created_by=admin_user,
        )
        assert sm.production_order == po

    def test_supplier_relation(self, supply, supplier, org_a, admin_user):
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('20'),
            supplier=supplier, created_by=admin_user,
        )
        assert sm.supplier == supplier

    def test_for_tenant_filter(self, supply, org_a, org_b, admin_user):
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('10'),
            created_by=admin_user,
        )
        StockMovement.objects.create(
            organization=org_b, supply=supply,
            movement_type='entry', quantity=Decimal('99'),
            created_by=admin_user,
        )
        assert StockMovement.objects.for_tenant(org_a).count() == 1
        assert StockMovement.objects.for_tenant(org_b).count() == 1

    def test_str(self, supply, org_a, admin_user):
        sm = StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('25'),
            created_by=admin_user,
        )
        assert 'Entrada' in str(sm)
        assert '25' in str(sm)
        assert 'kg' in str(sm)
        assert supply.name in str(sm)


# ═══════════════════════════════════════════════════════════════════
# Reagent
# ═══════════════════════════════════════════════════════════════════

class TestReagent:
    def test_creation(self, org_a, uom_ml):
        reagent = Reagent.objects.create(
            organization=org_a,
            code='REA-001',
            name='Solución Buffer pH 7',
            description='Buffer fosfato',
            preparation_instructions='Disolver en 1L de agua destilada.',
            yield_quantity=Decimal('1000'),
            yield_unit=uom_ml,
        )
        assert reagent.pk is not None
        assert reagent.code == 'REA-001'
        assert reagent.tracks_batch is True
        assert reagent.is_active is True
        assert reagent.organization == org_a

    def test_str_with_code(self, org_a, uom_ml):
        reagent = Reagent.objects.create(
            organization=org_a, code='REA-002', name='Titulante',
            yield_unit=uom_ml,
        )
        assert str(reagent) == 'REA-002 — Titulante'

    def test_str_without_code(self, org_a, uom_ml):
        reagent = Reagent.objects.create(
            organization=org_a, name='Indicador', yield_unit=uom_ml,
        )
        assert str(reagent) == 'Indicador'

    def test_yield_unit_relation(self, org_a, uom_ml):
        reagent = Reagent.objects.create(
            organization=org_a, name='Reactivo Y', yield_unit=uom_ml,
        )
        assert reagent.yield_unit == uom_ml

    def test_items_recipe_relation(self, org_a, supply, uom_kg, uom_ml):
        reagent = Reagent.objects.create(
            organization=org_a, name='Buffer', yield_unit=uom_ml,
        )
        item = ReagentItem.objects.create(
            reagent=reagent, supply=supply,
            quantity=Decimal('0.5'), unit=uom_kg,
        )
        assert reagent.items.count() == 1
        assert reagent.items.first() == item

    def test_soft_delete_reagent(self, org_a, uom_ml, admin_user):
        reagent = Reagent.objects.create(
            organization=org_a, name='Para Borrar', yield_unit=uom_ml,
        )
        pk = reagent.pk
        reagent.soft_delete(user=admin_user)
        assert Reagent.objects.for_tenant(org_a).filter(pk=pk).exists() is False
        assert Reagent.all_objects.filter(
            organization=org_a, pk=pk, is_deleted=True
        ).exists()


# ═══════════════════════════════════════════════════════════════════
# ReagentItem
# ═══════════════════════════════════════════════════════════════════

class TestReagentItem:
    @pytest.fixture
    def reagent(self, org_a, uom_ml):
        return Reagent.objects.create(
            organization=org_a, name='Reactivo Z', yield_unit=uom_ml,
        )

    def test_creation(self, reagent, supply, uom_kg):
        item = ReagentItem.objects.create(
            reagent=reagent, supply=supply,
            quantity=Decimal('2.5'), unit=uom_kg,
            notes='Agregar lentamente',
        )
        assert item.pk is not None
        assert item.reagent == reagent
        assert item.supply == supply
        assert item.quantity == Decimal('2.5')
        assert item.notes == 'Agregar lentamente'

    def test_str(self, reagent, supply, uom_kg):
        item = ReagentItem.objects.create(
            reagent=reagent, supply=supply,
            quantity=Decimal('1'), unit=uom_kg,
        )
        assert supply.name in str(item)
        assert reagent.name in str(item)

    def test_quantity_positive_minimum(self, reagent, supply, uom_kg):
        # 0.0001 es el mínimo válido
        item = ReagentItem(
            reagent=reagent, supply=supply,
            quantity=Decimal('0.0001'), unit=uom_kg,
        )
        item.full_clean()  # no lanza excepción

    def test_quantity_zero_fails_validation(self, reagent, supply, uom_kg):
        item = ReagentItem(
            reagent=reagent, supply=supply,
            quantity=Decimal('0'), unit=uom_kg,
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_quantity_negative_fails_validation(self, reagent, supply, uom_kg):
        item = ReagentItem(
            reagent=reagent, supply=supply,
            quantity=Decimal('-1'), unit=uom_kg,
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_cascade_on_reagent_delete(self, reagent, supply, uom_kg):
        ReagentItem.objects.create(
            reagent=reagent, supply=supply,
            quantity=Decimal('1'), unit=uom_kg,
        )
        assert ReagentItem.objects.count() == 1
        reagent.delete()
        assert ReagentItem.objects.count() == 0


# ═══════════════════════════════════════════════════════════════════
# ProductionOrder
# ═══════════════════════════════════════════════════════════════════

class TestProductionOrder:
    @pytest.fixture
    def reagent(self, org_a, uom_ml):
        return Reagent.objects.create(
            organization=org_a, name='Producto X', yield_unit=uom_ml,
        )

    @pytest.fixture
    def order(self, org_a, reagent, admin_user):
        return ProductionOrder.objects.create(
            organization=org_a, reagent=reagent,
            batch_number='LOTE-2025-001', quantity=Decimal('50'),
            created_by=admin_user,
        )

    def test_creation(self, order, reagent, org_a, admin_user):
        assert order.pk is not None
        assert order.batch_number == 'LOTE-2025-001'
        assert order.quantity == Decimal('50')
        assert order.status == 'planned'
        assert order.reagent == reagent
        assert order.created_by == admin_user
        assert order.organization == org_a

    def test_str(self, order):
        assert 'OP-LOTE-2025-001' in str(order)
        assert 'Producto X' in str(order)

    def test_status_flow_planned_to_in_progress(self, order):
        assert order.status == 'planned'
        order.status = 'in_progress'
        order.started_at = timezone.now()
        order.save()
        order.refresh_from_db()
        assert order.status == 'in_progress'

    def test_status_flow_in_progress_to_completed(self, order):
        order.status = 'in_progress'
        order.started_at = timezone.now()
        order.save()
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        order.refresh_from_db()
        assert order.status == 'completed'
        assert order.completed_at is not None

    def test_cancellation(self, order):
        assert order.status == 'planned'
        order.status = 'cancelled'
        order.save()
        order.refresh_from_db()
        assert order.status == 'cancelled'

    def test_notes_optional(self, order):
        assert order.notes == ''

    def test_reagent_relation(self, order, reagent):
        assert order.reagent == reagent
        assert reagent.production_orders.count() == 1

    def test_multiple_orders_same_batch_allowed(self, org_a, reagent, admin_user):
        """Nota: el modelo no tiene UniqueConstraint en batch_number."""
        ProductionOrder.objects.create(
            organization=org_a, reagent=reagent,
            batch_number='SAME-BATCH', quantity=Decimal('10'),
            created_by=admin_user,
        )
        po2 = ProductionOrder.objects.create(
            organization=org_a, reagent=reagent,
            batch_number='SAME-BATCH', quantity=Decimal('20'),
            created_by=admin_user,
        )
        assert po2.pk is not None


# ═══════════════════════════════════════════════════════════════════
# Tenant isolation
# ═══════════════════════════════════════════════════════════════════

class TestTenantIsolation:
    def test_category_isolation(self, org_a, org_b):
        Category.objects.create(organization=org_a, name='Solo A')
        Category.objects.create(organization=org_b, name='Solo B')
        names_a = set(Category.objects.for_tenant(org_a).values_list('name', flat=True))
        names_b = set(Category.objects.for_tenant(org_b).values_list('name', flat=True))
        assert 'Solo A' in names_a
        assert 'Solo B' not in names_a
        assert 'Solo B' in names_b
        assert 'Solo A' not in names_b

    def test_supply_isolation(self, org_a, org_b, category, uom_kg):
        cat_b = Category.objects.create(organization=org_b, name='Cat B')
        uom_b = UnitOfMeasure.objects.create(
            organization=org_b, name='Kilogramo', abbreviation='kg'
        )
        Supply.objects.create(
            organization=org_a, code='ISO-A', name='Insumo A',
            category=category, unit=uom_kg,
        )
        Supply.objects.create(
            organization=org_b, code='ISO-B', name='Insumo B',
            category=cat_b, unit=uom_b,
        )
        names_a = set(Supply.objects.for_tenant(org_a).values_list('name', flat=True))
        names_b = set(Supply.objects.for_tenant(org_b).values_list('name', flat=True))
        assert 'Insumo A' in names_a
        assert 'Insumo B' not in names_a
        assert 'Insumo B' in names_b
        assert 'Insumo A' not in names_b

    def test_stock_movement_isolation(self, supply, org_a, org_b, admin_user):
        s_b = Supply.objects.create(
            organization=org_b, code='INS-B', name='Insumo B',
            category=Category.objects.create(
                organization=org_b, name='Cat B'
            ),
            unit=UnitOfMeasure.objects.create(
                organization=org_b, name='Kilogramo', abbreviation='kg'
            ),
        )
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('10'),
            created_by=admin_user,
        )
        StockMovement.objects.create(
            organization=org_b, supply=s_b,
            movement_type='entry', quantity=Decimal('99'),
            created_by=admin_user,
        )
        assert StockMovement.objects.for_tenant(org_a).count() == 1
        assert StockMovement.objects.for_tenant(org_b).count() == 1
        assert StockMovement.objects.for_tenant(org_a).first().supply == supply
        assert StockMovement.objects.for_tenant(org_b).first().supply == s_b


# ═══════════════════════════════════════════════════════════════════
# Stock flow integration
# ═══════════════════════════════════════════════════════════════════

class TestStockFlowIntegration:
    def test_full_flow(self, supply, org_a, admin_user):
        # Paso 1: stock inicial en 0
        assert supply.current_stock == Decimal('0')
        assert supply.stock_status == 'low'

        # Paso 2: entrada de 50 unidades
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('50'),
            created_by=admin_user,
        )
        supply.refresh_from_db()
        assert supply.current_stock == Decimal('50')
        assert supply.stock_status == 'high'  # 50 >= stock_max=50

        # Paso 3: salida de 20 unidades — stock queda en 30
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='exit', quantity=Decimal('20'),
            created_by=admin_user,
        )
        supply.refresh_from_db()
        assert supply.current_stock == Decimal('30')
        assert supply.stock_status == 'ok'

        # Paso 4: ajuste negativo de 25 — stock baja a 5
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='adjustment', quantity=Decimal('-25'),
            created_by=admin_user,
        )
        supply.refresh_from_db()
        assert supply.current_stock == Decimal('5')
        assert supply.stock_status == 'low'  # 5 <= 10

        # Paso 5: entrada de 20 — stock sube a 25
        StockMovement.objects.create(
            organization=org_a, supply=supply,
            movement_type='entry', quantity=Decimal('20'),
            created_by=admin_user,
        )
        supply.refresh_from_db()
        assert supply.current_stock == Decimal('25')
        assert supply.stock_status == 'ok'
