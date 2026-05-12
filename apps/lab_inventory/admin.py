from django.contrib import admin
from .models import (
    Category, UnitOfMeasure, Supplier, Supply,
    Reagent, ReagentItem, Batch, ProductionOrder, StockMovement,
)


class TenantAdminMixin:
    """Filtra queryset por organización del usuario logueado."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization=request.user.organization)

    def save_model(self, request, obj, form, change):
        if not change and not obj.organization_id:
            obj.organization = request.user.organization
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'organization', 'created_at']
    list_filter = ['organization']
    search_fields = ['name']


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'abbreviation']


@admin.register(Supplier)
class SupplierAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'rif', 'contact_name', 'is_active', 'organization']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'rif']


@admin.register(Supply)
class SupplyAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit', 'is_active', 'organization']
    list_filter = ['organization', 'category', 'is_active']
    search_fields = ['name', 'code']


class ReagentItemInline(admin.TabularInline):
    model = ReagentItem
    extra = 1
    fields = ['supply', 'quantity', 'unit', 'notes']


@admin.register(Reagent)
class ReagentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'yield_quantity', 'yield_unit', 'is_active', 'organization']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'code']
    inlines = [ReagentItemInline]


@admin.register(Batch)
class BatchAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['batch_number', 'item', 'expiration_date', 'supplier', 'created_at', 'organization']
    list_filter = ['organization']
    search_fields = ['batch_number']
    readonly_fields = ['id', 'created_at']


@admin.register(ProductionOrder)
class ProductionOrderAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['__str__', 'reagent', 'batch_number', 'status', 'quantity', 'created_at']
    list_filter = ['organization', 'status']
    search_fields = ['batch_number', 'reagent__name']


@admin.register(StockMovement)
class StockMovementAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ['supply', 'movement_type', 'quantity', 'batch_number', 'created_at', 'organization']
    list_filter = ['organization', 'movement_type']
    search_fields = ['supply__name', 'batch_number']
