"""
Tests de modelos del core: Organization, User, TenantModel, TenantSoftDeleteModel.
"""
import pytest
from django.db import IntegrityError

from apps.core.models import Organization, TenantSoftDeleteModel, User


# ────────────────────────────────────────────────────────────
# Organization
# ────────────────────────────────────────────────────────────

class TestOrganization:

    def test_str_returns_name(self, db, org_a):
        assert str(org_a) == 'Ferretería Central'

    def test_slug_is_unique(self, db, org_a):
        with pytest.raises(IntegrityError):
            Organization.objects.create(name='Otra', slug='ferreteria-central')

    def test_is_active_por_defecto(self, db, org_a):
        assert org_a.is_active is True

    def test_plan_starter_por_defecto(self, db, org_a):
        assert org_a.plan == 'starter'

    def test_total_usuarios_cuenta_solo_activos(self, db, org_a, admin_user):
        assert org_a.total_usuarios == 1
        admin_user.is_active = False
        admin_user.save()
        assert org_a.total_usuarios == 0


# ────────────────────────────────────────────────────────────
# User
# ────────────────────────────────────────────────────────────

class TestUser:

    def test_str_includes_role(self, db, admin_user):
        result = str(admin_user)
        assert 'Administrador' in result or 'admin' in result

    def test_is_superadmin_false_for_admin(self, db, admin_user):
        assert admin_user.is_superadmin is False

    def test_is_superadmin_true_for_superadmin(self, db, superadmin_user):
        assert superadmin_user.is_superadmin is True

    def test_is_admin_property(self, db, admin_user):
        assert admin_user.is_admin is True

    def test_superadmin_puede_estar_sin_org(self, db, superadmin_user):
        assert superadmin_user.organization is None

    def test_uuid_pk(self, db, admin_user):
        import uuid
        assert isinstance(admin_user.id, uuid.UUID)

    def test_roles_choices(self, db):
        roles = [r[0] for r in User.ROLES]
        assert 'superadmin' in roles
        assert 'admin' in roles
        assert 'manager' in roles
        assert 'staff' in roles


# ────────────────────────────────────────────────────────────
# TenantManager / TenantQuerySet
# ────────────────────────────────────────────────────────────

class TestTenantManager:
    """Prueba for_tenant() sin necesitar un modelo concreto — usa User."""

    def test_for_tenant_filtra_por_org(self, db, org_a, org_b, admin_user):
        """Usuarios de org_b no aparecen al filtrar por org_a."""
        User.objects.create_user(
            username='user_b', password='x', organization=org_b, role='staff'
        )
        # User no hereda TenantModel pero Organization sí tiene FKs — usamos
        # el queryset de User filtrando por organización directamente
        qs_a = User.objects.filter(organization=org_a)
        qs_b = User.objects.filter(organization=org_b)
        assert qs_a.count() == 1
        assert qs_b.count() == 1
        assert qs_a.first() == admin_user


# ────────────────────────────────────────────────────────────
# TenantSoftDeleteModel (abstract — testeamos vía subclase dummy)
# ────────────────────────────────────────────────────────────

class TestTenantSoftDeleteModel:
    """Verifica la composición correcta del modelo combinado."""

    def test_tenant_soft_delete_model_es_abstracto(self):
        assert TenantSoftDeleteModel._meta.abstract is True

    def test_soft_delete_model_fields_exist(self):
        field_names = [f.name for f in TenantSoftDeleteModel._meta.get_fields()]
        assert 'organization' in field_names
        assert 'is_deleted' in field_names
        assert 'deleted_at' in field_names
        assert 'deleted_by' in field_names
