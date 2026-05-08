"""Tests HTTP de las vistas marcar_leida y marcar_todas_leidas."""
import pytest
from django.urls import reverse

from apps.notifications.models import Notification
from apps.notifications.tests.factories import NotificationFactory
from apps.lab_inventory.tests.factories import OrganizationFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def org():
    return OrganizationFactory()


@pytest.fixture
def other_org():
    return OrganizationFactory()


@pytest.fixture
def user(org):
    return UserFactory(organization=org, role='admin')


@pytest.fixture
def cli(client, user):
    client.force_login(user)
    return client


# ── marcar_leida ────────────────────────────────────────────────────

class TestMarcarLeida:
    def test_marks_own_notification(self, cli, user, org):
        n = NotificationFactory(organization=org, user=user, leida=False)
        resp = cli.post(reverse('notifications:marcar_leida', args=[n.pk]))
        assert resp.status_code == 200
        assert resp.json() == {'status': 'ok'}
        n.refresh_from_db()
        assert n.leida is True

    def test_get_method_not_allowed(self, cli, user, org):
        n = NotificationFactory(organization=org, user=user)
        resp = cli.get(reverse('notifications:marcar_leida', args=[n.pk]))
        assert resp.status_code == 405

    def test_anonymous_redirected(self, client, org, user):
        n = NotificationFactory(organization=org, user=user)
        resp = client.post(reverse('notifications:marcar_leida', args=[n.pk]))
        assert resp.status_code == 302

    def test_other_user_same_org_404(self, cli, org, user):
        """No puedes marcar como leída la notificación de otro usuario."""
        other_user = UserFactory(organization=org, role='staff')
        n = NotificationFactory(organization=org, user=other_user)
        resp = cli.post(reverse('notifications:marcar_leida', args=[n.pk]))
        assert resp.status_code == 404
        n.refresh_from_db()
        assert n.leida is False

    def test_other_org_404(self, cli, other_org):
        """REGRESIÓN: notificación de otra org debe retornar 404."""
        foreign_user = UserFactory(organization=other_org, role='admin')
        n = NotificationFactory(organization=other_org, user=foreign_user)
        resp = cli.post(reverse('notifications:marcar_leida', args=[n.pk]))
        assert resp.status_code == 404
        n.refresh_from_db()
        assert n.leida is False


# ── marcar_todas_leidas ─────────────────────────────────────────────

class TestMarcarTodasLeidas:
    def test_marks_all_own_unread(self, cli, user, org):
        NotificationFactory.create_batch(3, organization=org, user=user, leida=False)
        NotificationFactory(organization=org, user=user, leida=True)
        resp = cli.post(reverse('notifications:marcar_todas_leidas'))
        assert resp.status_code == 200
        unread = Notification.objects.filter(user=user, leida=False).count()
        assert unread == 0

    def test_does_not_mark_other_user(self, cli, user, org):
        other_user = UserFactory(organization=org, role='staff')
        n = NotificationFactory(organization=org, user=other_user, leida=False)
        cli.post(reverse('notifications:marcar_todas_leidas'))
        n.refresh_from_db()
        assert n.leida is False

    def test_does_not_mark_other_org(self, cli, other_org):
        """REGRESIÓN: el bulk update no debe afectar otras orgs."""
        foreign_user = UserFactory(organization=other_org, role='admin')
        n = NotificationFactory(organization=other_org, user=foreign_user, leida=False)
        cli.post(reverse('notifications:marcar_todas_leidas'))
        n.refresh_from_db()
        assert n.leida is False

    def test_get_method_not_allowed(self, cli):
        resp = cli.get(reverse('notifications:marcar_todas_leidas'))
        assert resp.status_code == 405

    def test_anonymous_redirected(self, client):
        resp = client.post(reverse('notifications:marcar_todas_leidas'))
        assert resp.status_code == 302
