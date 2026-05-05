import pytest
from django.test import RequestFactory


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def org_a(db):
    """Organización principal de pruebas."""
    from apps.core.models import Organization
    return Organization.objects.create(
        name='Ferretería Central',
        slug='ferreteria-central',
    )


@pytest.fixture
def org_b(db):
    """Organización secundaria para tests de aislamiento multi-tenant."""
    from apps.core.models import Organization
    return Organization.objects.create(
        name='Farmacia Sur',
        slug='farmacia-sur',
    )


@pytest.fixture
def admin_user(db, org_a):
    """Usuario admin asignado a org_a."""
    from apps.core.models import User
    return User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='adminpass',
        organization=org_a,
        role='admin',
    )


@pytest.fixture
def superadmin_user(db):
    """Superadmin sin organización (acceso global).

    Se usa create_user con is_superuser=True para que el CheckConstraint
    (role='superadmin' OR organization IS NOT NULL) pase en el primer INSERT.
    create_superuser no acepta role, así que crearía primero con role='staff' y org=None
    violando el constraint antes del segundo save.
    """
    from apps.core.models import User
    return User.objects.create_user(
        username='superadmin',
        email='super@test.com',
        password='superpass',
        role='superadmin',
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def auth_client(client, admin_user):
    """Cliente HTTP autenticado como admin."""
    client.force_login(admin_user)
    return client


# ── Lab Inventory fixtures ──────────────────────────────────────────

@pytest.fixture
def category(db, org_a):
    """Categoría de insumos en org_a."""
    from apps.lab_inventory.models import Category
    return Category.objects.create(
        organization=org_a,
        name='Reactivos Base',
        description='Reactivos base para preparación analítica',
    )


@pytest.fixture
def uom_kg(db, org_a):
    """Unidad de medida: Kilogramo."""
    from apps.lab_inventory.models import UnitOfMeasure
    return UnitOfMeasure.objects.create(
        organization=org_a,
        name='Kilogramo',
        abbreviation='kg',
    )


@pytest.fixture
def uom_ml(db, org_a):
    """Unidad de medida: Mililitro."""
    from apps.lab_inventory.models import UnitOfMeasure
    return UnitOfMeasure.objects.create(
        organization=org_a,
        name='Mililitro',
        abbreviation='ml',
    )


@pytest.fixture
def supplier(db, org_a):
    """Proveedor en org_a."""
    from apps.lab_inventory.models import Supplier
    return Supplier.objects.create(
        organization=org_a,
        name='Químicos del Sur',
        rif='J-12345678-9',
        contact_name='Juan Pérez',
        phone='+58-412-555-1234',
        email='juan@quimicossur.com',
        address='Av. Principal, Guanare',
    )


@pytest.fixture
def supply(db, org_a, category, uom_kg):
    """Insumo en org_a con stock_min=10."""
    from apps.lab_inventory.models import Supply
    return Supply.objects.create(
        organization=org_a,
        code='INS-001',
        name='Cloruro de Sodio',
        description='NaCl grado analítico',
        category=category,
        unit=uom_kg,
        stock_min=10,
        stock_max=50,
    )
