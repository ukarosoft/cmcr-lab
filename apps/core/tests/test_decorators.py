"""
Tests de decoradores: role_required, superadmin_required, tenant_required.
"""
import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory

from apps.core.decorators import role_required, superadmin_required, tenant_required


def _dummy_view(request, *args, **kwargs):
    return HttpResponse('OK', status=200)


def _make_request(rf, user, path='/', tenant=None):
    req = rf.get(path)
    req.user = user
    req.tenant = tenant
    req.session = {}
    req._messages = FallbackStorage(req)
    return req


class TestRoleRequired:

    def test_admin_accede_a_vista_admin(self, rf, admin_user, org_a):
        view = role_required('admin')(_dummy_view)
        req = _make_request(rf, admin_user, tenant=org_a)
        response = view(req)
        assert response.status_code == 200

    def test_staff_no_accede_a_vista_admin(self, db, rf, org_a):
        from apps.core.models import User
        staff = User.objects.create_user(
            username='staff', password='x', organization=org_a, role='staff'
        )
        view = role_required('admin')(_dummy_view)
        req = _make_request(rf, staff, tenant=org_a)
        response = view(req)
        assert response.status_code == 302

    def test_superadmin_accede_sin_importar_rol(self, rf, superadmin_user):
        view = role_required('admin', 'manager')(_dummy_view)
        req = _make_request(rf, superadmin_user)
        response = view(req)
        assert response.status_code == 200

    def test_usuario_no_autenticado_redirige_a_login(self, rf):
        view = role_required('admin')(_dummy_view)
        req = _make_request(rf, AnonymousUser())
        response = view(req)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_multiples_roles_permitidos(self, db, rf, org_a):
        from apps.core.models import User
        manager = User.objects.create_user(
            username='mgr', password='x', organization=org_a, role='manager'
        )
        view = role_required('admin', 'manager')(_dummy_view)
        req = _make_request(rf, manager, tenant=org_a)
        response = view(req)
        assert response.status_code == 200


class TestSuperadminRequired:

    def test_superadmin_accede(self, rf, superadmin_user):
        view = superadmin_required(_dummy_view)
        req = _make_request(rf, superadmin_user)
        response = view(req)
        assert response.status_code == 200

    def test_admin_normal_no_accede(self, rf, admin_user, org_a):
        view = superadmin_required(_dummy_view)
        req = _make_request(rf, admin_user, tenant=org_a)
        response = view(req)
        assert response.status_code == 302

    def test_anonimo_no_accede(self, rf):
        view = superadmin_required(_dummy_view)
        req = _make_request(rf, AnonymousUser())
        response = view(req)
        assert response.status_code == 302
        assert '/login/' in response.url


class TestTenantRequired:

    def test_con_tenant_accede(self, rf, admin_user, org_a):
        view = tenant_required(_dummy_view)
        req = _make_request(rf, admin_user, tenant=org_a)
        response = view(req)
        assert response.status_code == 200

    def test_sin_tenant_redirige(self, rf, admin_user):
        view = tenant_required(_dummy_view)
        req = _make_request(rf, admin_user, tenant=None)
        response = view(req)
        assert response.status_code == 302

    def test_anonimo_redirige_a_login(self, rf):
        view = tenant_required(_dummy_view)
        req = _make_request(rf, AnonymousUser())
        response = view(req)
        assert response.status_code == 302
        assert '/login/' in response.url
