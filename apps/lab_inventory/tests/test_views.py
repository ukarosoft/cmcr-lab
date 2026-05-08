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
from apps.lab_inventory.tests.factories import (
    OrganizationFactory,
    UserFactory,
    CategoryFactory,
    UnitOfMeasureFactory,
    SupplierFactory,
    SupplyFactory,
    ReagentFactory,
    ReagentItemFactory,
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
