"""Factories para Notification."""
import factory
from factory.django import DjangoModelFactory

from apps.notifications.models import Notification
from apps.lab_inventory.tests.factories import OrganizationFactory, UserFactory


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(
        UserFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    mensaje = factory.Sequence(lambda n: f'Mensaje de prueba {n}')
    tipo = 'info'
    leida = False
