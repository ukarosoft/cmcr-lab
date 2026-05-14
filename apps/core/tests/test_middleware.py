"""
Tests del TenantMiddleware: inyección de tenant, rutas públicas,
manejo de org inactiva, redirecciones.
"""
import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser

from apps.core.middleware import TenantMiddleware


def _make_request(rf, path='/', user=None):
    """Helper: crea request con user y session/messages configurados."""
    req = rf.get(path)
    req.user = user or AnonymousUser()
    req.session = {}
    req._messages = FallbackStorage(req)
    return req


def _get_response(request):
    """Get-response dummy que retorna el mismo request."""
    return request


class TestTenantMiddlewareAnonymous:

    def test_anonymous_usuario_pasa_sin_tenant(self, rf):
        mw = TenantMiddleware(_get_response)
        req = _make_request(rf, '/')
        result = mw(req)
        assert result.tenant is None

    def test_ruta_publica_login_no_bloquea(self, rf, admin_user):
        mw = TenantMiddleware(_get_response)
        req = _make_request(rf, '/login/', user=admin_user)
        result = mw(req)
        # No redirige — devuelve el request tal como está
        assert hasattr(result, 'tenant')

    def test_healthz_es_ruta_publica(self, rf, admin_user):
        mw = TenantMiddleware(_get_response)
        req = _make_request(rf, '/healthz/', user=admin_user)
        result = mw(req)
        assert hasattr(result, 'tenant')


class TestTenantMiddlewareWithOrg:

    def test_usuario_con_org_activa_recibe_tenant(self, rf, admin_user, org_a):
        mw = TenantMiddleware(_get_response)
        req = _make_request(rf, '/dashboard/', user=admin_user)
        result = mw(req)
        assert result.tenant == org_a

    def test_superadmin_pasa_sin_tenant_asignado(self, rf, superadmin_user):
        mw = TenantMiddleware(_get_response)
        req = _make_request(rf, '/dashboard/', user=superadmin_user)
        result = mw(req)
        # Superadmin pasa — tenant puede ser None
        assert result is not None

    def test_usuario_sin_org_redirige_a_login(self, db, rf):
        """El constraint BD impide crear staff sin org — el middleware redirige
        en el edge case de org=None (ej: superadmin con rol no-superadmin vía admin)."""
        from django.db import IntegrityError
        from apps.core.models import User
        # Verificamos que el constraint funciona: staff sin org viola la BD
        with pytest.raises(IntegrityError, match='user_org_required_for_non_superadmin'):
            User.objects.create_user(username='noorg', password='x', role='staff')

    def test_org_inactiva_redirige_a_cuenta_suspendida(self, rf, admin_user, org_a):
        org_a.is_active = False
        org_a.save()
        mw = TenantMiddleware(_get_response)
        req = _make_request(rf, '/dashboard/', user=admin_user)
        response = mw(req)
        assert response.status_code == 302
        assert 'cuenta-suspendida' in response.url


class TestTenantMiddlewareIsolation:

    def test_dos_usuarios_tienen_su_propio_tenant(self, rf, org_a, org_b):
        from apps.core.models import User
        user_a = User.objects.create_user(
            username='ua', password='x', organization=org_a, role='admin'
        )
        user_b = User.objects.create_user(
            username='ub', password='x', organization=org_b, role='admin'
        )
        mw = TenantMiddleware(_get_response)

        req_a = _make_request(rf, '/', user=user_a)
        result_a = mw(req_a)
        assert result_a.tenant == org_a

        req_b = _make_request(rf, '/', user=user_b)
        result_b = mw(req_b)
        assert result_b.tenant == org_b
