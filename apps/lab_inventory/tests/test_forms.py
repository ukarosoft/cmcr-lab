"""Tests directos de forms (sin pasar por la vista).

Foco: garantizar que los forms con argumento `tenant=` filtran sus
querysets de FK por organización. Esto previene bugs cross-org si una
vista futura olvida pasar tenant o si se usan los forms desde otro lugar.
"""
from decimal import Decimal

import pytest

from apps.lab_inventory.forms import (
    CategoryForm,
    UnitOfMeasureForm,
    SupplyForm,
    ReagentItemForm,
    ProductionOrderForm,
    StockMovementForm,
)
from apps.lab_inventory.tests.factories import (
    OrganizationFactory,
    SupplyFactory,
    ReagentFactory,
    SupplierFactory,
    UnitOfMeasureFactory,
    CategoryFactory,
)

pytestmark = pytest.mark.django_db


# ── ReagentItemForm ────────────────────────────────────────────────

class TestReagentItemForm:
    def test_supply_queryset_filtered_by_tenant(self):
        org = OrganizationFactory()
        other = OrganizationFactory()
        own_supply = SupplyFactory(organization=org)
        SupplyFactory(organization=other)

        form = ReagentItemForm(tenant=org)
        supplies = list(form.fields['supply'].queryset)
        assert own_supply in supplies
        assert all(s.organization == org for s in supplies)

    def test_without_tenant_does_not_crash(self):
        """Sin tenant, el queryset queda con su default (no filtrado).
        Esto NO debe usarse en producción pero el form no debe romper."""
        form = ReagentItemForm()
        assert form.fields['supply'].queryset is not None

    def test_invalid_quantity_zero(self, db):
        org = OrganizationFactory()
        supply = SupplyFactory(organization=org)
        unit = UnitOfMeasureFactory(organization=org)
        form = ReagentItemForm(
            data={'supply': str(supply.pk), 'quantity': '0',
                  'unit': str(unit.pk), 'notes': ''},
            tenant=org,
        )
        assert not form.is_valid()
        assert 'quantity' in form.errors


# ── ProductionOrderForm ────────────────────────────────────────────

class TestProductionOrderForm:
    def test_reagent_queryset_filtered_by_tenant(self):
        org = OrganizationFactory()
        other = OrganizationFactory()
        own_reagent = ReagentFactory(organization=org)
        ReagentFactory(organization=other)

        form = ProductionOrderForm(tenant=org)
        reagents = list(form.fields['reagent'].queryset)
        assert own_reagent in reagents
        assert all(r.organization == org for r in reagents)

    def test_invalid_quantity_zero(self, db):
        org = OrganizationFactory()
        reagent = ReagentFactory(organization=org)
        form = ProductionOrderForm(
            data={'reagent': str(reagent.pk), 'batch_number': 'X',
                  'quantity': '0', 'notes': ''},
            tenant=org,
        )
        assert not form.is_valid()
        assert 'quantity' in form.errors


# ── StockMovementForm ──────────────────────────────────────────────

class TestStockMovementForm:
    def test_supply_queryset_filtered_by_tenant(self):
        org = OrganizationFactory()
        other = OrganizationFactory()
        SupplyFactory(organization=org)
        SupplyFactory(organization=other)

        form = StockMovementForm(tenant=org)
        supplies = list(form.fields['supply'].queryset)
        assert all(s.organization == org for s in supplies)

    def test_supplier_queryset_filtered_by_tenant(self):
        org = OrganizationFactory()
        other = OrganizationFactory()
        SupplierFactory(organization=org)
        SupplierFactory(organization=other)

        form = StockMovementForm(tenant=org)
        suppliers = list(form.fields['supplier'].queryset)
        assert all(s.organization == org for s in suppliers)


# ── Forms simples (CategoryForm, UOMForm, SupplyForm) ──────────────

class TestSimpleForms:
    def test_category_form_valid(self, db):
        form = CategoryForm(data={'name': 'Buffers', 'description': 'desc'})
        assert form.is_valid()

    def test_category_form_blank_name_invalid(self, db):
        form = CategoryForm(data={'name': '', 'description': ''})
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_uom_form_valid(self, db):
        form = UnitOfMeasureForm(data={'name': 'Litro', 'abbreviation': 'L'})
        assert form.is_valid()

    def test_supply_form_valid(self, db):
        org = OrganizationFactory()
        cat = CategoryFactory(organization=org)
        unit = UnitOfMeasureFactory(organization=org)
        form = SupplyForm(data={
            'code': 'X-1', 'name': 'Insumo X', 'description': '',
            'category': str(cat.pk), 'unit': str(unit.pk),
            'stock_min': '0', 'stock_max': '0', 'is_active': True,
        })
        assert form.is_valid(), form.errors
