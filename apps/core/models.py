import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """Tenant — empresa cliente."""

    PLANES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField('nombre', max_length=200)
    slug       = models.SlugField(unique=True, help_text='Identificador URL único')
    is_active  = models.BooleanField('activa', default=True)
    plan       = models.CharField(max_length=20, choices=PLANES, default='starter')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def total_usuarios(self):
        # Nota: en listados usar annotate() para evitar N+1:
        # Organization.objects.annotate(n_users=Count('users', filter=Q(users__is_active=True)))
        return self.users.filter(is_active=True).count()


class User(AbstractUser):
    """Usuario del sistema con rol y organización."""

    ROLES = [
        ('superadmin', 'Super Admin'),
        ('admin',      'Administrador'),
        ('manager',    'Gerente'),
        ('staff',      'Empleado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='organización',
        related_name='users',
        help_text='Vacío solo para superadmins',
    )
    role = models.CharField('rol', max_length=20, choices=ROLES, default='staff')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        constraints = [
            # Garantiza a nivel de BD que solo los superadmin pueden no tener organización
            models.CheckConstraint(
                condition=(
                    models.Q(role='superadmin') |
                    models.Q(organization__isnull=False)
                ),
                name='user_org_required_for_non_superadmin',
                violation_error_message='Solo los superadmins pueden existir sin organización.',
            ),
        ]

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_staff_member(self):
        return self.role == 'staff'

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role != 'superadmin':
            self.role = 'superadmin'
        super().save(*args, **kwargs)


class TenantQuerySet(models.QuerySet):
    """QuerySet con filtrado multi-tenant incorporado."""

    def for_tenant(self, organization):
        """Filtra por organización. Uso: Model.objects.for_tenant(request.tenant)."""
        return self.filter(organization=organization)


class TenantManager(models.Manager):
    """Manager que retorna TenantQuerySet."""

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_tenant(self, organization):
        return self.get_queryset().for_tenant(organization)


class TenantModel(models.Model):
    """
    Clase base para todos los modelos que pertenecen a una organización.

    Uso en vistas:
        items = MiModelo.objects.for_tenant(request.tenant)

    Regla de oro: NUNCA usar .all() ni .filter() sin for_tenant() en vistas normales.
    """
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.PROTECT,
        verbose_name='organización',
    )

    objects = TenantManager()

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet con filtrado de borrado lógico."""

    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).active()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """Modelo base para borrado lógico."""
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self, user=None):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    class Meta:
        abstract = True


class TenantSoftDeleteQuerySet(TenantQuerySet):
    """
    QuerySet que combina filtrado de tenant + borrado lógico.
    Uso: MyModel.objects.for_tenant(request.tenant)  → solo activos del tenant
         MyModel.objects.all_with_deleted().for_tenant(org)  → incluye borrados
    """

    def active(self):
        return self.filter(is_deleted=False)

    def for_tenant(self, organization):
        return super().for_tenant(organization).active()


class TenantSoftDeleteManager(models.Manager):
    """Manager para modelos TenantSoftDeleteModel."""

    def get_queryset(self):
        return TenantSoftDeleteQuerySet(self.model, using=self._db).active()

    def for_tenant(self, organization):
        return TenantSoftDeleteQuerySet(self.model, using=self._db).for_tenant(organization)

    def all_with_deleted(self):
        """Acceso a todos los registros (incluye borrados lógicos)."""
        return TenantSoftDeleteQuerySet(self.model, using=self._db)


class TenantSoftDeleteModel(models.Model):
    """
    Modelo base para datos multi-tenant con borrado lógico.
    Usar en lugar de combinar TenantModel + SoftDeleteModel manualmente
    (la composición directa rompe el MRO y pierde filtros).

    Ejemplo:
        class Pedido(TenantSoftDeleteModel):
            numero = models.CharField(max_length=20)
    """
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.PROTECT,
        verbose_name='organización',
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    objects = TenantSoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self, user=None):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

    class Meta:
        abstract = True
