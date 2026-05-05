import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TenantModel, TenantSoftDeleteModel


class Category(TenantModel):
    """Categoría de insumos (Reactivo base, Solvente, Buffer, etc.)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('nombre', max_length=150)
    description = models.TextField('descripción', blank=True)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        indexes = [models.Index(fields=['organization', 'name'])]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_category_per_tenant'
            ),
        ]

    def __str__(self):
        return self.name


class UnitOfMeasure(TenantModel):
    """Unidad de medida (kg, L, mL, unidad, frasco, etc.)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('nombre', max_length=80)
    abbreviation = models.CharField('abreviatura', max_length=20)
    created_at = models.DateTimeField('creado', auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Unidad de medida'
        verbose_name_plural = 'Unidades de medida'
        indexes = [models.Index(fields=['organization', 'name'])]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'abbreviation'],
                name='unique_uom_abbr_per_tenant'
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.abbreviation})'


class Supplier(TenantModel):
    """Proveedor de insumos de laboratorio."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('nombre', max_length=200)
    rif = models.CharField('RIF', max_length=20, blank=True)
    contact_name = models.CharField('persona de contacto', max_length=150, blank=True)
    phone = models.CharField('teléfono', max_length=30, blank=True)
    email = models.EmailField('email', blank=True)
    address = models.TextField('dirección', blank=True)
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        indexes = [models.Index(fields=['organization', 'name'])]

    def __str__(self):
        return self.name


class Supply(TenantSoftDeleteModel):
    """Insumo de laboratorio — materia prima para preparar reactivos."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField('código', max_length=50, blank=True)
    name = models.CharField('nombre', max_length=250)
    description = models.TextField('descripción', blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name='categoría',
        related_name='supplies',
    )
    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        verbose_name='unidad de medida',
        related_name='supplies',
    )
    stock_min = models.DecimalField(
        'stock mínimo', max_digits=12, decimal_places=4, default=0
    )
    stock_max = models.DecimalField(
        'stock máximo', max_digits=12, decimal_places=4, default=0
    )
    tracks_batch = models.BooleanField(
        'control por lote',
        default=False,
        help_text='Si este insumo requiere trazabilidad por número de lote',
    )
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'name']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'code'],
                name='unique_supply_code_per_tenant',
            ),
        ]

    def __str__(self):
        if self.code:
            return f'{self.code} — {self.name}'
        return self.name

    @property
    def current_stock(self):
        """Calcula el stock actual sumando movimientos."""
        from django.db.models import Sum
        result = self.movements.for_tenant(self.organization).aggregate(
            total=Sum('quantity')
        )
        return result['total'] or Decimal('0')

    @property
    def stock_status(self):
        """Retorna 'low', 'ok', 'high' según el nivel de stock."""
        stock = self.current_stock
        if stock <= self.stock_min:
            return 'low'
        if self.stock_max > 0 and stock >= self.stock_max:
            return 'high'
        return 'ok'


class Reagent(TenantSoftDeleteModel):
    """Reactivo — producto final preparado a partir de insumos."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField('código', max_length=50, blank=True)
    name = models.CharField('nombre', max_length=250)
    description = models.TextField('descripción', blank=True)
    preparation_instructions = models.TextField(
        'instrucciones de preparación', blank=True
    )
    yield_quantity = models.DecimalField(
        'cantidad producida', max_digits=12, decimal_places=4, default=1
    )
    yield_unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        verbose_name='unidad de rendimiento',
        related_name='reagents',
    )
    tracks_batch = models.BooleanField('control por lote', default=True)
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Reactivo'
        verbose_name_plural = 'Reactivos'
        indexes = [models.Index(fields=['organization', 'name'])]

    def __str__(self):
        if self.code:
            return f'{self.code} — {self.name}'
        return self.name


class ReagentItem(models.Model):
    """Ítem de la receta — insumo necesario para preparar un reactivo."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reagent = models.ForeignKey(
        Reagent,
        on_delete=models.CASCADE,
        verbose_name='reactivo',
        related_name='items',
    )
    supply = models.ForeignKey(
        Supply,
        on_delete=models.PROTECT,
        verbose_name='insumo',
        related_name='recipe_usages',
    )
    quantity = models.DecimalField(
        'cantidad requerida', max_digits=12, decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
    )
    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        verbose_name='unidad',
    )
    notes = models.CharField('notas', max_length=200, blank=True)

    class Meta:
        ordering = ['supply__name']
        verbose_name = 'Ítem de receta'
        verbose_name_plural = 'Ítems de receta'

    def __str__(self):
        return f'{self.supply.name} → {self.reagent.name}'


class ProductionOrder(TenantModel):
    """Orden de producción de un reactivo."""
    STATUS_CHOICES = [
        ('planned', 'Planificada'),
        ('in_progress', 'En proceso'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reagent = models.ForeignKey(
        Reagent,
        on_delete=models.PROTECT,
        verbose_name='reactivo',
        related_name='production_orders',
    )
    batch_number = models.CharField('número de lote', max_length=80)
    quantity = models.DecimalField(
        'cantidad a producir', max_digits=12, decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
    )
    status = models.CharField(
        'estado', max_length=20, choices=STATUS_CHOICES, default='planned'
    )
    notes = models.TextField('observaciones', blank=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='creado por',
        related_name='+',
    )
    created_at = models.DateTimeField('creado', auto_now_add=True)
    started_at = models.DateTimeField('iniciado', null=True, blank=True)
    completed_at = models.DateTimeField('completado', null=True, blank=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Orden de producción'
        verbose_name_plural = 'Órdenes de producción'
        indexes = [
            models.Index(fields=['organization', 'batch_number']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', '-created_at']),
        ]

    def __str__(self):
        return f'OP-{self.batch_number} — {self.reagent.name}'


class StockMovement(TenantModel):
    """Movimiento de inventario — entrada, salida o ajuste."""
    MOVEMENT_TYPES = [
        ('entry', 'Entrada'),
        ('exit', 'Salida'),
        ('adjustment', 'Ajuste'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supply = models.ForeignKey(
        Supply,
        on_delete=models.PROTECT,
        verbose_name='insumo',
        related_name='movements',
    )
    movement_type = models.CharField(
        'tipo', max_length=15, choices=MOVEMENT_TYPES
    )
    quantity = models.DecimalField(
        'cantidad', max_digits=12, decimal_places=4,
    )
    batch_number = models.CharField('número de lote', max_length=80, blank=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='proveedor',
        related_name='movements',
    )
    production_order = models.ForeignKey(
        ProductionOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='orden de producción',
        related_name='movements',
    )
    reason = models.CharField('motivo', max_length=255, blank=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='registrado por',
        related_name='+',
    )
    created_at = models.DateTimeField('fecha', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Movimiento de stock'
        verbose_name_plural = 'Movimientos de stock'
        indexes = [
            models.Index(fields=['organization', 'supply']),
            models.Index(fields=['organization', 'movement_type']),
            models.Index(fields=['organization', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if self.movement_type == 'exit':
            self.quantity = -abs(self.quantity)
        elif self.movement_type == 'entry':
            self.quantity = abs(self.quantity)
        super().save(*args, **kwargs)

    def __str__(self):
        tipo = self.get_movement_type_display()
        return f'{tipo} de {self.quantity} {self.supply.unit.abbreviation} — {self.supply.name}'
