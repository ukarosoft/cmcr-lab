"""Factories de fixtures con factory_boy para tests de lab_inventory.

Convención Ukarasoft: usar factory_boy en lugar de construir objetos a mano.
Ventaja: cada test obtiene datos independientes, sin colisiones, con valores
realistas y mínimos campos requeridos.
"""
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.core.models import Organization, User
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


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: f'Lab Test {n}')
    slug = factory.Sequence(lambda n: f'lab-test-{n}')
    is_active = True
    plan = 'starter'


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@test.local')
    role = 'admin'
    organization = factory.SubFactory(OrganizationFactory)
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'testpass123')
        user = model_class.objects.create_user(*args, password=password, **kwargs)
        return user


class SuperadminFactory(UserFactory):
    role = 'superadmin'
    organization = None
    is_staff = True
    is_superuser = True


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f'Categoría {n}')
    description = factory.Faker('sentence', locale='es_ES')


class UnitOfMeasureFactory(DjangoModelFactory):
    class Meta:
        model = UnitOfMeasure

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f'Unidad {n}')
    abbreviation = factory.Sequence(lambda n: f'u{n}')


class SupplierFactory(DjangoModelFactory):
    class Meta:
        model = Supplier

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f'Proveedor {n}')
    rif = factory.Sequence(lambda n: f'J-{n:08d}-0')
    contact_name = factory.Faker('name', locale='es_ES')
    phone = '+58-412-555-0000'
    email = factory.LazyAttribute(lambda o: f'contacto+{o.rif}@proveedor.test')
    is_active = True


class SupplyFactory(DjangoModelFactory):
    class Meta:
        model = Supply

    organization = factory.SubFactory(OrganizationFactory)
    code = factory.Sequence(lambda n: f'INS-{n:04d}')
    name = factory.Sequence(lambda n: f'Insumo {n}')
    description = factory.Faker('sentence', locale='es_ES')
    category = factory.SubFactory(
        CategoryFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    unit = factory.SubFactory(
        UnitOfMeasureFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    stock_min = Decimal('10')
    stock_max = Decimal('100')
    is_active = True


class ReagentFactory(DjangoModelFactory):
    class Meta:
        model = Reagent

    organization = factory.SubFactory(OrganizationFactory)
    code = factory.Sequence(lambda n: f'REA-{n:04d}')
    name = factory.Sequence(lambda n: f'Reactivo {n}')
    yield_quantity = Decimal('1')
    yield_unit = factory.SubFactory(
        UnitOfMeasureFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    is_active = True


class ReagentItemFactory(DjangoModelFactory):
    class Meta:
        model = ReagentItem

    organization = factory.SubFactory(OrganizationFactory)
    reagent = factory.SubFactory(
        ReagentFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    supply = factory.SubFactory(
        SupplyFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    quantity = Decimal('1')
    unit = factory.SubFactory(
        UnitOfMeasureFactory,
        organization=factory.SelfAttribute('..organization'),
    )


class ProductionOrderFactory(DjangoModelFactory):
    class Meta:
        model = ProductionOrder

    organization = factory.SubFactory(OrganizationFactory)
    reagent = factory.SubFactory(
        ReagentFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    batch_number = factory.Sequence(lambda n: f'L{n:05d}')
    quantity = Decimal('5')
    status = 'planned'


class StockMovementFactory(DjangoModelFactory):
    class Meta:
        model = StockMovement

    organization = factory.SubFactory(OrganizationFactory)
    supply = factory.SubFactory(
        SupplyFactory,
        organization=factory.SelfAttribute('..organization'),
    )
    movement_type = 'entry'
    quantity = Decimal('50')
