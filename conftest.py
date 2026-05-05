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
