"""Tests HTTP de vistas de lab_inventory.

Cobertura:
- Dashboard
- CRUDs (Category, UOM, Supplier, Supply, Reagent)
- Reagent items (add/delete) — incluye cross-org rejection
- Stock movements (create) — incluye filtrado de queryset
- Production orders (create/start/complete/cancel) — incluye reversión y stock check
- Aislamiento multi-tenant (regresiones de auditoría 2026-05-05)
- Permisos (login_required + role_required)
"""
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.notifications.models import Notification
from apps.lab_inventory.models import (
    Category,
    UnitOfMeasure,
    Supplier,
    Supply,
    Reagent,
    ReagentItem,
    Batch,
    ProductionOrder,
    StockMovement,
)
from apps.lab_inventory.tests.factories import (
    OrganizationFactory,
    UserFactory,
    CategoryFactory,
    UnitOfMeasureFactory,
    SupplierFactory,
    SupplyFactory,
    ReagentFactory,
    ReagentItemFactory,
    BatchFactory,
    ProductionOrderFactory,
    StockMovementFactory,
)

pytestmark = pytest.mark.django_db


# ── Fixtures de la suite ────────────────────────────────────────────

@pytest.fixture
def org():
    return OrganizationFactory()


@pytest.fixture
def other_org():
    return OrganizationFactory()


@pytest.fixture
def admin(org):
    return UserFactory(organization=org, role='admin')


@pytest.fixture
def staff(org):
    return UserFactory(organization=org, role='staff')


@pytest.fixture
def other_admin(other_org):
    return UserFactory(organization=other_org, role='admin')


@pytest.fixture
def cli(client, admin):
    client.force_login(admin)
    return client


@pytest.fixture
def cli_staff(client, staff):
    client.force_login(staff)
    return client


@pytest.fixture
def cli_other(client, other_admin):
    client.force_login(other_admin)
    return client


# ═══════════════════════════════════════════════════════════════════
# Auth / permisos
# ═══════════════════════════════════════════════════════════════════

class TestAuthRequired:
    def test_dashboard_redirects_anonymous(self, client):
        resp = client.get(reverse('lab_inventory:dashboard'))
        assert resp.status_code == 302
        assert '/login/' in resp.url

    def test_supply_list_redirects_anonymous(self, client):
        resp = client.get(reverse('lab_inventory:supply_list'))
        assert resp.status_code == 302

    def test_staff_can_view_lists(self, cli_staff):
        resp = cli_staff.get(reverse('lab_inventory:supply_list'))
        assert resp.status_code == 200

    def test_staff_blocked_on_supply_create(self, cli_staff):
        """Staff no debe poder crear insumos (solo admin/manager)."""
        resp = cli_staff.get(reverse('lab_inventory:supply_create'))
        # role_required redirige a login con mensaje
        assert resp.status_code == 302


# ═══════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════

class TestDashboard:
    def test_renders_for_admin(self, cli):
        resp = cli.get(reverse('lab_inventory:dashboard'))
        assert resp.status_code == 200
        assert b'dashboard' in resp.content.lower() or resp.context is not None

    def test_low_stock_only_includes_own_org(self, cli, org, other_org, admin):
        """Bug histórico: dashboard debe ignorar supplies de otra org."""
        own_supply = SupplyFactory(organization=org, stock_min=100)
        StockMovementFactory(
            organization=org, supply=own_supply,
            movement_type='entry', quantity=Decimal('1'),
        )
        # Otra org con supply en stock bajo — NO debe aparecer
        SupplyFactory(organization=other_org, stock_min=999)

        resp = cli.get(reverse('lab_inventory:dashboard'))
        assert resp.status_code == 200
        low_items = list(resp.context['low_stock_items'])
        assert own_supply in low_items
        assert all(s.organization == org for s in low_items)

    def test_counts_only_own_org(self, cli, org, other_org):
        SupplyFactory.create_batch(3, organization=org)
        SupplyFactory.create_batch(5, organization=other_org)
        resp = cli.get(reverse('lab_inventory:dashboard'))
        assert resp.context['total_supplies'] == 3


# ═══════════════════════════════════════════════════════════════════
# Category CRUD
# ═══════════════════════════════════════════════════════════════════

class TestCategoryCRUD:
    def test_create_assigns_tenant(self, cli, org):
        resp = cli.post(reverse('lab_inventory:category_create'), {
            'name': 'Reactivos Base',
            'description': 'desc',
        })
        assert resp.status_code == 302
        cat = Category.objects.get(name='Reactivos Base')
        assert cat.organization == org

    def test_list_only_own_org(self, cli, org, other_org):
        CategoryFactory(organization=org, name='Mía')
        CategoryFactory(organization=other_org, name='Ajena')
        resp = cli.get(reverse('lab_inventory:category_list'))
        assert resp.status_code == 200
        cats = list(resp.context['categories'])
        assert len(cats) == 1
        assert cats[0].name == 'Mía'

    def test_update_cross_org_returns_404(self, cli, other_org):
        foreign = CategoryFactory(organization=other_org)
        resp = cli.post(
            reverse('lab_inventory:category_update', args=[foreign.pk]),
            {'name': 'Hackeado', 'description': ''},
        )
        assert resp.status_code == 404

    def test_delete_cross_org_returns_404(self, cli, other_org):
        foreign = CategoryFactory(organization=other_org)
        resp = cli.post(reverse('lab_inventory:category_delete', args=[foreign.pk]))
        assert resp.status_code == 404
        assert Category.objects.filter(pk=foreign.pk).exists()


# ═══════════════════════════════════════════════════════════════════
# UnitOfMeasure CRUD
# ═══════════════════════════════════════════════════════════════════

class TestUOMCRUD:
    def test_create_assigns_tenant(self, cli, org):
        resp = cli.post(reverse('lab_inventory:uom_create'), {
            'name': 'Litro', 'abbreviation': 'L',
        })
        assert resp.status_code == 302
        u = UnitOfMeasure.objects.get(abbreviation='L')
        assert u.organization == org

    def test_update_cross_org_returns_404(self, cli, other_org):
        foreign = UnitOfMeasureFactory(organization=other_org)
        resp = cli.get(reverse('lab_inventory:uom_update', args=[foreign.pk]))
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# Supplier CRUD
# ═══════════════════════════════════════════════════════════════════

class TestSupplierCRUD:
    def test_create_assigns_tenant(self, cli, org):
        resp = cli.post(reverse('lab_inventory:supplier_create'), {
            'name': 'Químicos Andinos',
            'rif': 'J-99999999-9',
            'contact_name': '',
            'phone': '',
            'email': '',
            'address': '',
            'is_active': 'on',
        })
        assert resp.status_code == 302
        s = Supplier.objects.get(name='Químicos Andinos')
        assert s.organization == org

    def test_search_filters_by_query(self, cli, org):
        SupplierFactory(organization=org, name='Reactivos Caracas')
        SupplierFactory(organization=org, name='Plásticos Mérida')
        resp = cli.get(reverse('lab_inventory:supplier_list'), {'q': 'Caracas'})
        suppliers = list(resp.context['suppliers'])
        assert len(suppliers) == 1


# ═══════════════════════════════════════════════════════════════════
# Supply CRUD
# ═══════════════════════════════════════════════════════════════════

class TestSupplyCRUD:
    def test_create_assigns_tenant(self, cli, org):
        cat = CategoryFactory(organization=org)
        unit = UnitOfMeasureFactory(organization=org)
        resp = cli.post(reverse('lab_inventory:supply_create'), {
            'code': 'NaCl-01',
            'name': 'Cloruro',
            'description': '',
            'category': str(cat.pk),
            'unit': str(unit.pk),
            'stock_min': '10',
            'stock_max': '100',
            'is_active': 'on',
        })
        assert resp.status_code == 302, resp.context['form'].errors if resp.context else resp.content
        s = Supply.objects.get(code='NaCl-01')
        assert s.organization == org

    def test_create_form_only_shows_own_categories(self, cli, org, other_org):
        CategoryFactory(organization=org, name='Mía')
        CategoryFactory(organization=other_org, name='Ajena')
        resp = cli.get(reverse('lab_inventory:supply_create'))
        assert resp.status_code == 200
        cats = list(resp.context['form'].fields['category'].queryset)
        assert all(c.organization == org for c in cats)

    def test_detail_cross_org_returns_404(self, cli, other_org):
        foreign = SupplyFactory(organization=other_org)
        resp = cli.get(reverse('lab_inventory:supply_detail', args=[foreign.pk]))
        assert resp.status_code == 404

    def test_update_cross_org_returns_404(self, cli, other_org):
        foreign = SupplyFactory(organization=other_org)
        resp = cli.post(
            reverse('lab_inventory:supply_update', args=[foreign.pk]),
            {'code': 'X', 'name': 'X', 'description': '',
             'category': str(foreign.category.pk), 'unit': str(foreign.unit.pk),
             'stock_min': '0', 'stock_max': '0', 'is_active': 'on'},
        )
        assert resp.status_code == 404

    def test_delete_cross_org_returns_404(self, cli, other_org):
        foreign = SupplyFactory(organization=other_org)
        resp = cli.post(reverse('lab_inventory:supply_delete', args=[foreign.pk]))
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# Reagent CRUD
# ═══════════════════════════════════════════════════════════════════

class TestReagentCRUD:
    def test_create_assigns_tenant(self, cli, org):
        unit = UnitOfMeasureFactory(organization=org)
        resp = cli.post(reverse('lab_inventory:reagent_create'), {
            'code': 'REA-X',
            'name': 'Reactivo X',
            'description': '',
            'preparation_instructions': '',
            'yield_quantity': '1',
            'yield_unit': str(unit.pk),
            'stock_min': '0',
            'stock_max': '0',
            'is_active': 'on',
        })
        assert resp.status_code == 302
        r = Reagent.objects.get(code='REA-X')
        assert r.organization == org

    def test_detail_cross_org_returns_404(self, cli, other_org):
        foreign = ReagentFactory(organization=other_org)
        resp = cli.get(reverse('lab_inventory:reagent_detail', args=[foreign.pk]))
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# ReagentItem (FBV) — bug histórico 2026-05-05
# ═══════════════════════════════════════════════════════════════════

class TestReagentItem:
    def test_add_assigns_tenant(self, cli, org):
        reagent = ReagentFactory(organization=org)
        supply = SupplyFactory(organization=org)
        unit = UnitOfMeasureFactory(organization=org)
        resp = cli.post(
            reverse('lab_inventory:reagent_item_add', args=[reagent.pk]),
            {'supply': str(supply.pk), 'quantity': '2',
             'unit': str(unit.pk), 'notes': ''},
        )
        assert resp.status_code == 302
        item = ReagentItem.objects.get(reagent=reagent)
        assert item.organization == org

    def test_add_cross_org_reagent_returns_404(self, cli, other_org):
        """No debes poder agregar items a un reactivo de otra org."""
        foreign_reagent = ReagentFactory(organization=other_org)
        resp = cli.post(
            reverse('lab_inventory:reagent_item_add', args=[foreign_reagent.pk]),
            {},
        )
        assert resp.status_code == 404

    def test_delete_cross_org_returns_404(self, cli, other_org):
        """REGRESIÓN bug 2026-05-05: borrar item de otra org debe fallar."""
        foreign_item = ReagentItemFactory(organization=other_org)
        resp = cli.post(
            reverse('lab_inventory:reagent_item_delete', args=[foreign_item.pk]),
        )
        assert resp.status_code == 404
        assert ReagentItem.objects.filter(pk=foreign_item.pk).exists()

    def test_delete_own_org_succeeds(self, cli, org):
        item = ReagentItemFactory(organization=org)
        resp = cli.post(
            reverse('lab_inventory:reagent_item_delete', args=[item.pk]),
        )
        assert resp.status_code == 302
        assert not ReagentItem.objects.filter(pk=item.pk).exists()


# ═══════════════════════════════════════════════════════════════════
# StockMovement CRUD
# ═══════════════════════════════════════════════════════════════════

class TestStockMovement:
    def test_create_assigns_tenant_and_user(self, cli, admin, org):
        supply = SupplyFactory(organization=org)
        resp = cli.post(reverse('lab_inventory:movement_create'), {
            'supply': str(supply.pk),
            'movement_type': 'entry',
            'quantity': '50',
            'batch_number': '',
            'supplier': '',
            'reason': 'Compra inicial',
        })
        assert resp.status_code == 302
        sm = StockMovement.objects.get(supply=supply)
        assert sm.organization == org
        assert sm.created_by == admin
        assert sm.quantity == Decimal('50')

    def test_create_form_supply_queryset_filtered_by_tenant(self, cli, org, other_org):
        SupplyFactory(organization=org)
        SupplyFactory(organization=other_org)
        resp = cli.get(reverse('lab_inventory:movement_create'))
        supplies = list(resp.context['form'].fields['supply'].queryset)
        assert all(s.organization == org for s in supplies)
        assert len(supplies) == 1


# ═══════════════════════════════════════════════════════════════════
# ProductionOrder CRUD + ciclo de vida (FBVs críticas)
# ═══════════════════════════════════════════════════════════════════

class TestProductionOrder:
    def test_create_assigns_tenant_and_user(self, cli, admin, org):
        reagent = ReagentFactory(organization=org)
        resp = cli.post(reverse('lab_inventory:order_create'), {
            'reagent': str(reagent.pk),
            'batch_number': 'L-2026-001',
            'quantity': '5',
            'notes': '',
        })
        assert resp.status_code == 302
        po = ProductionOrder.objects.get(batch_number='L-2026-001')
        assert po.organization == org
        assert po.created_by == admin
        assert po.status == 'planned'

    def test_detail_cross_org_returns_404(self, cli, other_org):
        foreign = ProductionOrderFactory(organization=other_org)
        resp = cli.get(reverse('lab_inventory:order_detail', args=[foreign.pk]))
        assert resp.status_code == 404


class TestProductionOrderStart:
    def test_start_consumes_stock(self, cli, org, admin):
        """Iniciar la orden crea movimientos exit y cambia estado."""
        unit = UnitOfMeasureFactory(organization=org)
        supply = SupplyFactory(organization=org, unit=unit)
        # Stock disponible
        StockMovementFactory(
            organization=org, supply=supply,
            movement_type='entry', quantity=Decimal('100'),
        )
        reagent = ReagentFactory(organization=org, yield_quantity=Decimal('1'),
                                 yield_unit=unit)
        ReagentItemFactory(
            organization=org, reagent=reagent, supply=supply,
            unit=unit, quantity=Decimal('2'),
        )
        order = ProductionOrderFactory(
            organization=org, reagent=reagent, quantity=Decimal('5'),
        )

        resp = cli.post(reverse('lab_inventory:order_start', args=[order.pk]))
        assert resp.status_code == 302

        order.refresh_from_db()
        assert order.status == 'in_progress'
        assert order.started_at is not None

        # 1 movimiento de salida creado
        exits = StockMovement.objects.filter(
            production_order=order, movement_type='exit',
        )
        assert exits.count() == 1
        assert exits.first().quantity == Decimal('-10')  # 2 * 5 = 10, signo negativo

    def test_start_cross_org_returns_404(self, cli, other_org):
        """REGRESIÓN: no se debe poder iniciar orden de otra org."""
        foreign = ProductionOrderFactory(organization=other_org)
        resp = cli.post(reverse('lab_inventory:order_start', args=[foreign.pk]))
        assert resp.status_code == 404

    def test_start_with_insufficient_stock_does_not_consume(self, cli, org):
        unit = UnitOfMeasureFactory(organization=org)
        supply = SupplyFactory(organization=org, unit=unit)
        # Sin movimientos de entrada → stock 0
        reagent = ReagentFactory(organization=org, yield_quantity=Decimal('1'),
                                 yield_unit=unit)
        ReagentItemFactory(
            organization=org, reagent=reagent, supply=supply,
            unit=unit, quantity=Decimal('5'),
        )
        order = ProductionOrderFactory(
            organization=org, reagent=reagent, quantity=Decimal('1'),
        )
        resp = cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        assert resp.status_code == 200
        assert resp.context.get('errors')

        order.refresh_from_db()
        assert order.status == 'planned'
        assert StockMovement.objects.filter(production_order=order).count() == 0

    def test_start_already_in_progress_is_idempotent(self, cli, org):
        order = ProductionOrderFactory(organization=org, status='in_progress')
        resp = cli.post(reverse('lab_inventory:order_start', args=[order.pk]))
        assert resp.status_code == 302
        order.refresh_from_db()
        assert order.status == 'in_progress'


class TestProductionOrderComplete:
    def test_complete_sets_status(self, cli, org):
        order = ProductionOrderFactory(organization=org, status='in_progress')
        resp = cli.post(reverse('lab_inventory:order_complete', args=[order.pk]))
        assert resp.status_code == 302
        order.refresh_from_db()
        assert order.status == 'completed'
        assert order.completed_at is not None

    def test_complete_cross_org_returns_404(self, cli, other_org):
        foreign = ProductionOrderFactory(organization=other_org, status='in_progress')
        resp = cli.post(reverse('lab_inventory:order_complete', args=[foreign.pk]))
        assert resp.status_code == 404

    def test_complete_planned_does_nothing(self, cli, org):
        order = ProductionOrderFactory(organization=org, status='planned')
        cli.post(reverse('lab_inventory:order_complete', args=[order.pk]))
        order.refresh_from_db()
        assert order.status == 'planned'


class TestProductionOrderCancel:
    def test_cancel_planned_order(self, cli, org):
        order = ProductionOrderFactory(organization=org, status='planned')
        resp = cli.post(reverse('lab_inventory:order_cancel', args=[order.pk]))
        assert resp.status_code == 302
        order.refresh_from_db()
        assert order.status == 'cancelled'

    def test_cancel_in_progress_reverses_movements(self, cli, org):
        """Cancelar orden iniciada crea entradas compensatorias."""
        unit = UnitOfMeasureFactory(organization=org)
        supply = SupplyFactory(organization=org, unit=unit)
        order = ProductionOrderFactory(
            organization=org, status='in_progress',
        )
        # Movimiento de salida previo (simulando consumo)
        StockMovementFactory(
            organization=org, supply=supply, production_order=order,
            movement_type='exit', quantity=Decimal('20'),
        )

        resp = cli.post(reverse('lab_inventory:order_cancel', args=[order.pk]))
        assert resp.status_code == 302

        order.refresh_from_db()
        assert order.status == 'cancelled'

        movements = StockMovement.objects.filter(production_order=order)
        # 1 exit original + 1 entry compensatoria = 2
        assert movements.count() == 2
        entries = movements.filter(movement_type='entry')
        assert entries.count() == 1
        assert entries.first().quantity == Decimal('20')

    def test_cancel_cross_org_returns_404(self, cli, other_org):
        foreign = ProductionOrderFactory(organization=other_org, status='planned')
        resp = cli.post(reverse('lab_inventory:order_cancel', args=[foreign.pk]))
        assert resp.status_code == 404

    def test_cancel_completed_order_does_nothing(self, cli, org):
        order = ProductionOrderFactory(organization=org, status='completed')
        cli.post(reverse('lab_inventory:order_cancel', args=[order.pk]))
        order.refresh_from_db()
        assert order.status == 'completed'


# ═══════════════════════════════════════════════════════════════════
# List views — aislamiento básico
# ═══════════════════════════════════════════════════════════════════

class TestListIsolation:
    def test_supply_list_isolation(self, cli, org, other_org):
        SupplyFactory.create_batch(2, organization=org)
        SupplyFactory.create_batch(3, organization=other_org)
        resp = cli.get(reverse('lab_inventory:supply_list'))
        assert len(list(resp.context['supplies'])) == 2

    def test_reagent_list_isolation(self, cli, org, other_org):
        ReagentFactory.create_batch(2, organization=org)
        ReagentFactory.create_batch(3, organization=other_org)
        resp = cli.get(reverse('lab_inventory:reagent_list'))
        assert len(list(resp.context['reagents'])) == 2

    def test_movement_list_isolation(self, cli, org, other_org):
        StockMovementFactory.create_batch(2, organization=org)
        StockMovementFactory.create_batch(4, organization=other_org)
        resp = cli.get(reverse('lab_inventory:movement_list'))
        assert len(list(resp.context['movements'])) == 2

    def test_order_list_isolation(self, cli, org, other_org):
        ProductionOrderFactory.create_batch(2, organization=org)
        ProductionOrderFactory.create_batch(3, organization=other_org)
        resp = cli.get(reverse('lab_inventory:order_list'))
        assert len(list(resp.context['orders'])) == 2

    def test_batch_list_isolation(self, cli, org, other_org):
        BatchFactory.create_batch(2, organization=org)
        BatchFactory.create_batch(5, organization=other_org)
        resp = cli.get(reverse('lab_inventory:batch_list'))
        assert len(list(resp.context['batches'])) == 2


# ── Tests de Batch (P2, P3) ──────────────────────────────────────────

class TestBatchModel:
    """Tests unitarios del modelo Batch."""

    def test_batch_creation_with_supply(self, org):
        batch = BatchFactory(organization=org)
        assert batch.supply is not None
        assert batch.reagent is None
        assert batch.item == batch.supply

    def test_batch_creation_with_reagent(self, org):
        reagent = ReagentFactory(organization=org)
        batch = BatchFactory(organization=org, supply=None, reagent=reagent)
        assert batch.supply is None
        assert batch.reagent is not None
        assert batch.item == batch.reagent

    def test_batch_xor_constraint(self, org):
        """No se puede crear un batch con supply Y reagent a la vez."""
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Batch.objects.create(
                organization=org,
                supply=supply,
                reagent=reagent,
                batch_number='INVALID',
            )

    def test_batch_xor_constraint_both_null(self, org):
        """No se puede crear un batch sin supply ni reagent."""
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Batch.objects.create(
                organization=org,
                supply=None,
                reagent=None,
                batch_number='INVALID',
            )

    def test_batch_current_stock(self, org):
        supply = SupplyFactory(organization=org)
        batch = BatchFactory(organization=org, supply=supply)
        StockMovementFactory(organization=org, supply=supply, batch=batch,
                             movement_type='entry', quantity=Decimal('100'))
        StockMovementFactory(organization=org, supply=supply, batch=batch,
                             movement_type='exit', quantity=Decimal('30'))
        assert batch.current_stock == Decimal('70')

    def test_batch_is_expired(self, org):
        from datetime import date, timedelta
        batch_expired = BatchFactory(
            organization=org,
            expiration_date=date.today() - timedelta(days=1),
        )
        batch_valid = BatchFactory(
            organization=org,
            expiration_date=date.today() + timedelta(days=30),
        )
        batch_no_date = BatchFactory(organization=org, expiration_date=None)
        assert batch_expired.is_expired is True
        assert batch_valid.is_expired is False
        assert batch_no_date.is_expired is False

    def test_batch_days_until_expiry(self, org):
        from datetime import date, timedelta
        batch = BatchFactory(
            organization=org,
            expiration_date=date.today() + timedelta(days=15),
        )
        assert batch.days_until_expiry == 15

    def test_batch_days_until_expiry_none(self, org):
        batch = BatchFactory(organization=org, expiration_date=None)
        assert batch.days_until_expiry is None


class TestBatchViews:
    """Tests de vistas de Batch."""

    def test_batch_list_renders(self, cli, org):
        BatchFactory.create_batch(3, organization=org)
        resp = cli.get(reverse('lab_inventory:batch_list'))
        assert resp.status_code == 200
        assert len(list(resp.context['batches'])) == 3

    def test_batch_list_filter_expired(self, cli, org):
        from datetime import date, timedelta
        BatchFactory(organization=org, expiration_date=date.today() - timedelta(days=5))
        BatchFactory(organization=org, expiration_date=date.today() + timedelta(days=60))
        resp = cli.get(reverse('lab_inventory:batch_list') + '?expired=1')
        assert len(list(resp.context['batches'])) == 1

    def test_batch_list_filter_expiring(self, cli, org):
        from datetime import date, timedelta
        BatchFactory(organization=org, expiration_date=date.today() + timedelta(days=10))
        BatchFactory(organization=org, expiration_date=date.today() + timedelta(days=60))
        resp = cli.get(reverse('lab_inventory:batch_list') + '?expiring=1')
        assert len(list(resp.context['batches'])) == 1

    def test_batch_create(self, cli, org):
        supply = SupplyFactory(organization=org)
        supplier = SupplierFactory(organization=org)
        resp = cli.post(reverse('lab_inventory:batch_create'), {
            'supply': supply.pk,
            'batch_number': 'LOT-TEST-001',
            'expiration_date': '2027-06-15',
            'supplier': supplier.pk,
            'notes': 'Test batch',
        })
        assert resp.status_code == 302
        assert Batch.objects.for_tenant(org).count() == 1
        b = Batch.objects.for_tenant(org).first()
        assert b.batch_number == 'LOT-TEST-001'
        assert str(b.expiration_date) == '2027-06-15'

    def test_batch_create_staff_blocked(self, cli_staff):
        resp = cli_staff.get(reverse('lab_inventory:batch_create'))
        assert resp.status_code == 302  # redirect to login


# ── Tests de Reagent Stock (P1) ──────────────────────────────────────

class TestReagentStock:
    """Tests del stock de reactivos producidos."""

    def test_complete_creates_reagent_stock_entry(self, cli, org):
        """Al completar una OP, se registra entrada de stock del reactivo."""
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        item = ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('10'))
        # Stock de insumo suficiente
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('200'))
        order = ProductionOrderFactory(organization=org, reagent=reagent, quantity=Decimal('5'))
        # Iniciar la orden (consume insumos)
        cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        # Completar la orden
        cli.get(reverse('lab_inventory:order_complete', args=[order.pk]))
        order.refresh_from_db()
        assert order.status == 'completed'
        # Debe existir un movimiento de entrada del reactivo
        reagent_entry = StockMovement.objects.filter(
            reagent=reagent, movement_type='entry', production_order=order
        )
        assert reagent_entry.exists()
        assert reagent_entry.first().quantity == Decimal('5')
        # El reactivo debe tener stock
        assert reagent.current_stock == Decimal('5')

    def test_reagent_current_stock_after_multiple_productions(self, cli, org):
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('2'))
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('1000'))
        # Primera OP
        o1 = ProductionOrderFactory(organization=org, reagent=reagent, quantity=Decimal('10'))
        cli.get(reverse('lab_inventory:order_start', args=[o1.pk]))
        cli.get(reverse('lab_inventory:order_complete', args=[o1.pk]))
        # Segunda OP
        o2 = ProductionOrderFactory(organization=org, reagent=reagent, quantity=Decimal('15'))
        cli.get(reverse('lab_inventory:order_start', args=[o2.pk]))
        cli.get(reverse('lab_inventory:order_complete', args=[o2.pk]))
        assert reagent.current_stock == Decimal('25')

    def test_cancel_in_progress_does_not_create_reagent_entry(self, cli, org):
        """Cancelar una OP en proceso no crea entrada de reactivo."""
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('5'))
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('500'))
        order = ProductionOrderFactory(organization=org, reagent=reagent, quantity=Decimal('3'))
        cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        cli.get(reverse('lab_inventory:order_cancel', args=[order.pk]))
        # No debe haber entrada de reactivo
        assert not StockMovement.objects.filter(reagent=reagent).exists()
        assert reagent.current_stock == Decimal('0')

    def test_reagent_stock_status(self, org):
        reagent = ReagentFactory(organization=org, stock_min=Decimal('5'), stock_max=Decimal('50'))
        assert reagent.stock_status == 'low'  # stock = 0 <= 5
        StockMovement.objects.create(
            organization=org, reagent=reagent,
            movement_type='entry', quantity=Decimal('10'),
        )
        assert reagent.stock_status == 'ok'
        StockMovement.objects.create(
            organization=org, reagent=reagent,
            movement_type='entry', quantity=Decimal('45'),
        )
        assert reagent.stock_status == 'high'  # 55 >= 50

    def test_movement_supply_xor_reagent_constraint(self, org):
        """Un movimiento debe tener supply XOR reagent, no ambos."""
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            StockMovement.objects.create(
                organization=org, supply=supply, reagent=reagent,
                movement_type='entry', quantity=Decimal('10'),
            )

    def test_complete_creates_batch_for_reagent(self, cli, org):
        """Al completar una OP, se crea un lote asociado al reactivo."""
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('1'))
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('100'))
        order = ProductionOrderFactory(organization=org, reagent=reagent, quantity=Decimal('5'))
        cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        cli.get(reverse('lab_inventory:order_complete', args=[order.pk]))
        batch = Batch.objects.filter(reagent=reagent).first()
        assert batch is not None
        assert batch.batch_number == order.batch_number


# ── Tests de validación stock negativo (P4) y proveedor inactivo (P10) ──

class TestStockValidation:
    """Tests de validación de stock y filtrado de proveedores."""

    def test_exit_movement_with_insufficient_stock_rejected(self, cli, org):
        supply = SupplyFactory(organization=org)
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('10'))
        resp = cli.post(reverse('lab_inventory:movement_create'), {
            'supply': supply.pk,
            'movement_type': 'exit',
            'quantity': '50',
            'batch_number': '',
            'supplier': '',
            'reason': 'Test',
        })
        assert resp.status_code == 200  # form re-rendered with error
        form = resp.context['form']
        assert any('Stock insuficiente' in e for e in form.non_field_errors())

    def test_exit_movement_with_sufficient_stock_accepted(self, cli, org):
        supply = SupplyFactory(organization=org)
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('100'))
        resp = cli.post(reverse('lab_inventory:movement_create'), {
            'supply': supply.pk,
            'movement_type': 'exit',
            'quantity': '30',
            'batch_number': '',
            'supplier': '',
            'reason': 'Uso',
        })
        assert resp.status_code == 302

    def test_adjustment_negative_allowed(self, cli, org):
        """Los ajustes negativos deben permitirse sin validación de stock."""
        supply = SupplyFactory(organization=org)
        resp = cli.post(reverse('lab_inventory:movement_create'), {
            'supply': supply.pk,
            'movement_type': 'adjustment',
            'quantity': '-20',
            'batch_number': '',
            'supplier': '',
            'reason': 'Corrección conteo',
        })
        assert resp.status_code == 302

    def test_inactive_supplier_excluded_from_movement_form(self, cli, org):
        active = SupplierFactory(organization=org, is_active=True)
        inactive = SupplierFactory(organization=org, is_active=False)
        resp = cli.get(reverse('lab_inventory:movement_create'))
        supplier_qs = resp.context['form'].fields['supplier'].queryset
        assert active in supplier_qs
        assert inactive not in supplier_qs


# ── Tests de audit trail updated_by (P7) ──────────────────────────────

class TestAuditTrail:
    """Tests de updated_by en modelos editables."""

    def test_update_category_sets_updated_by(self, cli, admin, org):
        cat = CategoryFactory(organization=org)
        cli.post(reverse('lab_inventory:category_update', args=[cat.pk]), {
            'name': 'Nombre editado',
            'description': 'Desc editada',
        })
        cat.refresh_from_db()
        assert cat.updated_by == admin

    def test_create_category_does_not_set_updated_by(self, cli, org):
        cli.post(reverse('lab_inventory:category_create'), {
            'name': 'Nueva cat',
            'description': '',
        })
        cat = Category.objects.for_tenant(org).first()
        assert cat.updated_by is None

    def test_production_order_start_sets_updated_by(self, cli, admin, org):
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('1'))
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('100'))
        order = ProductionOrderFactory(organization=org, reagent=reagent)
        cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        order.refresh_from_db()
        assert order.updated_by == admin

    def test_production_order_complete_sets_updated_by(self, cli, admin, org):
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('1'))
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('100'))
        order = ProductionOrderFactory(organization=org, reagent=reagent)
        cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        cli.get(reverse('lab_inventory:order_complete', args=[order.pk]))
        order.refresh_from_db()
        assert order.updated_by == admin


# ── Tests de notificaciones automáticas (P9) ──────────────────────────

class TestAutoNotifications:
    """Tests de signals que generan notificaciones."""

    def test_low_stock_creates_notification(self, org):
        admin_user = UserFactory(organization=org, role='admin')
        supply = SupplyFactory(organization=org, stock_min=Decimal('20'))
        StockMovement.objects.create(
            organization=org, supply=supply,
            movement_type='entry', quantity=Decimal('5'),
        )
        notifs = Notification.objects.for_tenant(org).filter(user=admin_user, tipo='warning')
        assert notifs.exists()
        assert 'Stock bajo' in notifs.first().mensaje

    def test_no_notification_when_stock_ok(self, org):
        admin_user = UserFactory(organization=org, role='admin')
        supply = SupplyFactory(organization=org, stock_min=Decimal('5'))
        StockMovement.objects.create(
            organization=org, supply=supply,
            movement_type='entry', quantity=Decimal('50'),
        )
        notifs = Notification.objects.for_tenant(org).filter(user=admin_user, tipo='warning')
        assert not notifs.exists()

    def test_op_completed_creates_notification(self, cli, org):
        admin_user = UserFactory(organization=org, role='admin')
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('1'))
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('100'))
        order = ProductionOrderFactory(organization=org, reagent=reagent)
        cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        cli.get(reverse('lab_inventory:order_complete', args=[order.pk]))
        notifs = Notification.objects.for_tenant(org).filter(
            user=admin_user, tipo='success', mensaje__contains='completada',
        )
        assert notifs.exists()

    def test_op_cancelled_creates_notification(self, cli, org):
        admin_user = UserFactory(organization=org, role='admin')
        supply = SupplyFactory(organization=org)
        reagent = ReagentFactory(organization=org)
        ReagentItemFactory(organization=org, reagent=reagent, supply=supply, quantity=Decimal('1'))
        StockMovementFactory(organization=org, supply=supply, movement_type='entry', quantity=Decimal('100'))
        order = ProductionOrderFactory(organization=org, reagent=reagent)
        cli.get(reverse('lab_inventory:order_start', args=[order.pk]))
        cli.get(reverse('lab_inventory:order_cancel', args=[order.pk]))
        notifs = Notification.objects.for_tenant(org).filter(
            user=admin_user, tipo='warning', mensaje__contains='cancelada',
        )
        assert notifs.exists()

    def test_notification_only_for_same_tenant(self, org, other_org):
        admin_own = UserFactory(organization=org, role='admin')
        admin_other = UserFactory(organization=other_org, role='admin')
        supply = SupplyFactory(organization=org, stock_min=Decimal('20'))
        StockMovement.objects.create(
            organization=org, supply=supply,
            movement_type='entry', quantity=Decimal('5'),
        )
        assert Notification.objects.filter(user=admin_own).exists()
        assert not Notification.objects.filter(user=admin_other).exists()


# ── Tests de exportación CSV (P6) ──────────────────────────────────────

class TestCSVExports:
    """Tests de exportación CSV."""

    def test_export_supplies_csv(self, cli, org):
        SupplyFactory(organization=org)
        resp = cli.get(reverse('lab_inventory:export_supplies'))
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'text/csv'
        assert 'insumos.csv' in resp['Content-Disposition']

    def test_export_movements_csv(self, cli, org):
        StockMovementFactory(organization=org)
        resp = cli.get(reverse('lab_inventory:export_movements'))
        assert resp.status_code == 200
        assert 'movimientos.csv' in resp['Content-Disposition']

    def test_export_orders_csv(self, cli, org):
        ProductionOrderFactory(organization=org)
        resp = cli.get(reverse('lab_inventory:export_orders'))
        assert resp.status_code == 200
        assert 'ordenes.csv' in resp['Content-Disposition']

    def test_export_batches_csv(self, cli, org):
        BatchFactory(organization=org)
        resp = cli.get(reverse('lab_inventory:export_batches'))
        assert resp.status_code == 200
        assert 'lotes.csv' in resp['Content-Disposition']

    def test_export_csv_tenant_isolation(self, cli, org, other_org):
        SupplyFactory(organization=org, name='MiInsumo')
        SupplyFactory(organization=other_org, name='OtroInsumo')
        resp = cli.get(reverse('lab_inventory:export_supplies'))
        content = resp.content.decode('utf-8')
        assert 'MiInsumo' in content
        assert 'OtroInsumo' not in content

    def test_export_csv_staff_blocked(self, cli_staff):
        resp = cli_staff.get(reverse('lab_inventory:export_supplies'))
        assert resp.status_code == 302
