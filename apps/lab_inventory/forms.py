from django import forms
from .models import (
    Category, UnitOfMeasure, Supplier, Supply,
    Reagent, ReagentItem, ProductionOrder, StockMovement,
)


class BaseForm(forms.ModelForm):
    """Agrega input-base a todos los widgets automáticamente."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'input-base {css}'.strip()
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = css


class CategoryForm(BaseForm):
    class Meta:
        model = Category
        fields = ['name', 'description']


class UnitOfMeasureForm(BaseForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['name', 'abbreviation']


class SupplierForm(BaseForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'rif', 'contact_name',
            'phone', 'email', 'address', 'is_active',
        ]


class SupplyForm(BaseForm):
    class Meta:
        model = Supply
        fields = [
            'code', 'name', 'description', 'category',
            'unit', 'stock_min', 'stock_max', 'tracks_batch', 'is_active',
        ]


class ReagentForm(BaseForm):
    class Meta:
        model = Reagent
        fields = [
            'code', 'name', 'description', 'preparation_instructions',
            'yield_quantity', 'yield_unit', 'tracks_batch', 'is_active',
        ]


class ReagentItemForm(BaseForm):
    class Meta:
        model = ReagentItem
        fields = ['supply', 'quantity', 'unit', 'notes']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['supply'].queryset = Supply.objects.for_tenant(self.tenant)


class ProductionOrderForm(BaseForm):
    class Meta:
        model = ProductionOrder
        fields = ['reagent', 'batch_number', 'quantity', 'notes']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['reagent'].queryset = Reagent.objects.for_tenant(self.tenant)


class StockMovementForm(BaseForm):
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
