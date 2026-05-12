from django import forms
from .models import (
    Category, UnitOfMeasure, Supplier, Supply,
    Reagent, ReagentItem, Batch, ProductionOrder, StockMovement,
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
            'yield_quantity', 'yield_unit', 'stock_min', 'stock_max',
            'tracks_batch', 'is_active',
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


class BatchForm(BaseForm):
    class Meta:
        model = Batch
        fields = [
            'supply', 'batch_number', 'expiration_date',
            'supplier', 'notes',
        ]
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['supply'].queryset = Supply.objects.for_tenant(self.tenant)
            self.fields['supplier'].queryset = Supplier.objects.for_tenant(self.tenant).filter(is_active=True)


class StockMovementForm(BaseForm):
    class Meta:
        model = StockMovement
        fields = [
            'supply', 'movement_type', 'quantity',
            'batch_number', 'supplier', 'production_order', 'reason',
        ]

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['supply'].queryset = Supply.objects.for_tenant(self.tenant)
            self.fields['supplier'].queryset = Supplier.objects.for_tenant(self.tenant).filter(is_active=True)
            self.fields['production_order'].queryset = ProductionOrder.objects.for_tenant(self.tenant)

    def clean(self):
        cleaned = super().clean()
        movement_type = cleaned.get('movement_type')
        supply = cleaned.get('supply')
        quantity = cleaned.get('quantity')
        if movement_type == 'exit' and supply and quantity:
            current = supply.current_stock
            if current < abs(quantity):
                raise forms.ValidationError(
                    f'Stock insuficiente de {supply.name}: '
                    f'disponible {current} {supply.unit.abbreviation}, '
                    f'solicitado {abs(quantity)} {supply.unit.abbreviation}'
                )
        return cleaned
