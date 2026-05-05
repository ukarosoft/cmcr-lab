from django import forms
from .models import (
    Category, UnitOfMeasure, Supplier, Supply,
    Reagent, ReagentItem, ProductionOrder, StockMovement,
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']


class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['name', 'abbreviation']


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'rif', 'contact_name',
            'phone', 'email', 'address', 'is_active',
        ]


class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = [
            'code', 'name', 'description', 'category',
            'unit', 'stock_min', 'stock_max', 'tracks_batch', 'is_active',
        ]


class ReagentForm(forms.ModelForm):
    class Meta:
        model = Reagent
        fields = [
            'code', 'name', 'description', 'preparation_instructions',
            'yield_quantity', 'yield_unit', 'tracks_batch', 'is_active',
        ]


class ReagentItemForm(forms.ModelForm):
    class Meta:
        model = ReagentItem
        fields = ['supply', 'quantity', 'unit', 'notes']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['supply'].queryset = Supply.objects.for_tenant(self.tenant)


class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = ['reagent', 'batch_number', 'quantity', 'notes']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['reagent'].queryset = Reagent.objects.for_tenant(self.tenant)


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = [
            'supply', 'movement_type', 'quantity',
            'batch_number', 'supplier', 'reason',
        ]

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['supply'].queryset = Supply.objects.for_tenant(self.tenant)
            self.fields['supplier'].queryset = Supplier.objects.for_tenant(self.tenant)
