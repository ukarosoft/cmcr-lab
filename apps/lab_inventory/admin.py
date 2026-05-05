from django.contrib import admin
from .models import (
    Category, UnitOfMeasure, Supplier, Supply,
    Reagent, ReagentItem, ProductionOrder, StockMovement,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'created_at']
    list_filter = ['organization']
    search_fields = ['name']


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'abbreviation']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'rif', 'contact_name', 'is_active', 'organization']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'rif']


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit', 'is_active', 'organization']
    list_filter = ['organization', 'category', 'is_active']
    search_fields = ['name', 'code']


class ReagentItemInline(admin.TabularInline):
    model = ReagentItem
    extra = 1
    fields = ['supply', 'quantity', 'unit', 'notes']


@admin.register(Reagent)
class ReagentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'yield_quantity', 'yield_unit', 'is_active', 'organization']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'code']
    inlines = [ReagentItemInline]


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'reagent', 'batch_number', 'status', 'quantity', 'created_at']
    list_filter = ['organization', 'status']
    search_fields = ['batch_number', 'reagent__name']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['supply', 'movement_type', 'quantity', 'batch_number', 'created_at', 'organization']
    list_filter = ['organization', 'movement_type']
    search_fields = ['supply__name', 'batch_number']
