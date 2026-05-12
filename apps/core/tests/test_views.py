"""
Tests de vistas del core: login, logout, dashboard, healthz.
"""
import pytest
from django.urls import reverse


class TestHealthz:

    def test_healthz_devuelve_200(self, client):
        response = client.get('/healthz/')
        assert response.status_code == 200

    def test_healthz_devuelve_json_ok(self, client):
        import json
        response = client.get('/healthz/')
        data = json.loads(response.content)
        assert data['status'] == 'ok'

    def test_healthz_sin_autenticacion(self, client):
        """Healthz es público — no redirige a login."""
        response = client.get('/healthz/')
        assert response.status_code == 200


class TestLoginView:

    def test_login_get_muestra_formulario(self, client):
        response = client.get(reverse('core:login'))
        assert response.status_code == 200

    def test_login_post_credenciales_correctas(self, client, admin_user):
        response = client.post(reverse('core:login'), {
            'username': 'admin',
            'password': 'adminpass',
        })
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_login_post_credenciales_incorrectas(self, client):
        response = client.post(reverse('core:login'), {
            'username': 'noexiste',
            'password': 'wrongpass',
        })
        assert response.status_code == 200
        assert b'incorrectos' in response.content

    def test_usuario_autenticado_redirige_a_dashboard(self, auth_client):
        response = auth_client.get(reverse('core:login'))
        assert response.status_code == 302


class TestDashboardView:

    def test_dashboard_requiere_login(self, client):
        response = client.get(reverse('core:dashboard'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_dashboard_accesible_autenticado(self, auth_client):
        response = auth_client.get(reverse('core:dashboard'))
        assert response.status_code == 302
        assert reverse('lab_inventory:dashboard') in response.url


class TestLogoutView:

    def test_logout_redirige_a_login(self, auth_client):
        response = auth_client.get(reverse('core:logout'))
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_logout_cierra_sesion(self, auth_client, client):
        auth_client.get(reverse('core:logout'))
        response = client.get(reverse('core:dashboard'))
        assert response.status_code == 302


class TestCuentaSuspendida:

    def test_cuenta_suspendida_accesible(self, client):
        response = client.get(reverse('core:cuenta_suspendida'))
        assert response.status_code in [200, 403]


class TestPasswordReset:
    """Tests del flujo de recuperación de contraseña (P8)."""

    def test_password_reset_form_renders(self, client):
        response = client.get(reverse('core:password_reset'))
        assert response.status_code == 200
        assert 'Recuperar contraseña' in str(response.content, 'utf-8')

    @pytest.mark.django_db
    def test_password_reset_post_valid_email_redirects(self, client, admin_user):
        response = client.post(reverse('core:password_reset'), {
            'email': admin_user.email,
        })
        assert response.status_code == 302
        assert '/password-reset/done/' in response.url

    @pytest.mark.django_db
    def test_password_reset_post_sends_email(self, client, admin_user, mailoutbox):
        client.post(reverse('core:password_reset'), {
            'email': admin_user.email,
        })
        assert len(mailoutbox) == 1
        assert 'CMCR Lab' in mailoutbox[0].subject

    @pytest.mark.django_db
    def test_password_reset_nonexistent_email_no_leak(self, client):
        """POST con email inexistente redirige igual (no revela info)."""
        response = client.post(reverse('core:password_reset'), {
            'email': 'noexiste@test.com',
        })
        assert response.status_code == 302

    def test_password_reset_done_renders(self, client):
        response = client.get('/password-reset/done/')
        assert response.status_code == 200
        assert 'Correo enviado' in str(response.content, 'utf-8')

    def test_login_has_forgot_password_link(self, client):
        response = client.get(reverse('core:login'))
        assert 'password-reset' in str(response.content, 'utf-8')
