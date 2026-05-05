from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView,
)
from .models import (
    Category, UnitOfMeasure, Supplier, Supply,
    Reagent, ReagentItem, ProductionOrder, StockMovement,
)
from .forms import (
    CategoryForm, UnitOfMeasureForm, SupplierForm,
    SupplyForm, ReagentForm, ReagentItemForm,
    ProductionOrderForm, StockMovementForm,
)


# ────────────── Dashboard ──────────────

@login_required
def dashboard(request):
    tenant = request.tenant
    supplies = Supply.objects.for_tenant(tenant)
    reagents = Reagent.objects.for_tenant(tenant)
    orders = ProductionOrder.objects.for_tenant(tenant)

    total_supplies = supplies.count()
    total_reagents = reagents.count()
    low_stock_count = sum(1 for s in supplies if s.stock_status == 'low')
    pending_orders = orders.filter(status='planned').count()
    in_progress_orders = orders.filter(status='in_progress').count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    recent_movements = (
        StockMovement.objects.for_tenant(tenant).select_related('supply', 'created_by')[:10]
    )

    # Supplies with stock below minimum (alert)
    low_stock_items = [s for s in supplies if s.stock_status == 'low']

    ctx = {
        'total_supplies': total_supplies,
        'total_reagents': total_reagents,
        'low_stock_count': low_stock_count,
        'low_stock_items': low_stock_items,
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'recent_movements': recent_movements,
    }
    return render(request, 'lab_inventory/dashboard.html', ctx)


# ────────────── Categorías ──────────────

class CategoryListView(ListView):
    model = Category
    template_name = 'lab_inventory/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.for_tenant(self.request.tenant)

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_category_table.html']
        return [self.template_name]


class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:category_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)


class CategoryUpdateView(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:category_list')

    def get_queryset(self):
        return Category.objects.for_tenant(self.request.tenant)


class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:category_list')

    def get_queryset(self):
        return Category.objects.for_tenant(self.request.tenant)


# ────────────── Unidades de medida ──────────────

class UOMListView(ListView):
    model = UnitOfMeasure
    template_name = 'lab_inventory/uom_list.html'
    context_object_name = 'uoms'

    def get_queryset(self):
        return UnitOfMeasure.objects.for_tenant(self.request.tenant)

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_uom_table.html']
        return [self.template_name]


class UOMCreateView(CreateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:uom_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)


class UOMUpdateView(UpdateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:uom_list')

    def get_queryset(self):
        return UnitOfMeasure.objects.for_tenant(self.request.tenant)


class UOMDeleteView(DeleteView):
    model = UnitOfMeasure
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:uom_list')

    def get_queryset(self):
        return UnitOfMeasure.objects.for_tenant(self.request.tenant)


# ────────────── Proveedores ──────────────

class SupplierListView(ListView):
    model = Supplier
    template_name = 'lab_inventory/supplier_list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        qs = Supplier.objects.for_tenant(self.request.tenant)
        if q := self.request.GET.get('q'):
            qs = qs.filter(
                Q(name__icontains=q) | Q(rif__icontains=q)
            )
        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_supplier_table.html']
        return [self.template_name]


class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'lab_inventory/supplier_form.html'
    success_url = reverse_lazy('lab_inventory:supplier_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)


class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'lab_inventory/supplier_form.html'
    success_url = reverse_lazy('lab_inventory:supplier_list')

    def get_queryset(self):
        return Supplier.objects.for_tenant(self.request.tenant)


class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:supplier_list')

    def get_queryset(self):
        return Supplier.objects.for_tenant(self.request.tenant)


# ────────────── Insumos ──────────────

class SupplyListView(ListView):
    model = Supply
    template_name = 'lab_inventory/supply_list.html'
    context_object_name = 'supplies'

    def get_queryset(self):
        qs = Supply.objects.for_tenant(self.request.tenant).select_related(
            'category', 'unit'
        )
        if q := self.request.GET.get('q'):
            qs = qs.filter(
                Q(name__icontains=q) | Q(code__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Add stock status for each item
        for s in ctx['supplies']:
            s._stock_status = s.stock_status
            s._current_stock = s.current_stock
        return ctx

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_supply_table.html']
        return [self.template_name]


class SupplyCreateView(CreateView):
    model = Supply
    form_class = SupplyForm
    template_name = 'lab_inventory/supply_form.html'
    success_url = reverse_lazy('lab_inventory:supply_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.for_tenant(self.request.tenant)
        form.fields['unit'].queryset = UnitOfMeasure.objects.for_tenant(self.request.tenant)
        return form


class SupplyUpdateView(UpdateView):
    model = Supply
    form_class = SupplyForm
    template_name = 'lab_inventory/supply_form.html'
    success_url = reverse_lazy('lab_inventory:supply_list')

    def get_queryset(self):
        return Supply.objects.for_tenant(self.request.tenant)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.for_tenant(self.request.tenant)
        form.fields['unit'].queryset = UnitOfMeasure.objects.for_tenant(self.request.tenant)
        return form


class SupplyDetailView(DetailView):
    model = Supply
    template_name = 'lab_inventory/supply_detail.html'
    context_object_name = 'supply'

    def get_queryset(self):
        return Supply.objects.for_tenant(self.request.tenant).select_related(
            'category', 'unit'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['movements'] = (
            StockMovement.objects.for_tenant(self.request.tenant)
            .filter(supply=self.object)
            .select_related('supplier', 'production_order')
            .order_by('-created_at')[:50]
        )
        ctx['current_stock'] = self.object.current_stock
        ctx['stock_status'] = self.object.stock_status
        return ctx


class SupplyDeleteView(DeleteView):
    model = Supply
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:supply_list')

    def get_queryset(self):
        return Supply.objects.for_tenant(self.request.tenant)


# ────────────── Reactivos ──────────────

class ReagentListView(ListView):
    model = Reagent
    template_name = 'lab_inventory/reagent_list.html'
    context_object_name = 'reagents'

    def get_queryset(self):
        qs = Reagent.objects.for_tenant(self.request.tenant)
        if q := self.request.GET.get('q'):
            qs = qs.filter(
                Q(name__icontains=q) | Q(code__icontains=q)
            )
        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_reagent_table.html']
        return [self.template_name]


class ReagentCreateView(CreateView):
    model = Reagent
    form_class = ReagentForm
    template_name = 'lab_inventory/reagent_form.html'
    success_url = reverse_lazy('lab_inventory:reagent_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['yield_unit'].queryset = UnitOfMeasure.objects.for_tenant(self.request.tenant)
        return form


class ReagentUpdateView(UpdateView):
    model = Reagent
    form_class = ReagentForm
    template_name = 'lab_inventory/reagent_form.html'
    success_url = reverse_lazy('lab_inventory:reagent_list')

    def get_queryset(self):
        return Reagent.objects.for_tenant(self.request.tenant)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['yield_unit'].queryset = UnitOfMeasure.objects.for_tenant(self.request.tenant)
        return form


class ReagentDetailView(DetailView):
    model = Reagent
    template_name = 'lab_inventory/reagent_detail.html'
    context_object_name = 'reagent'

    def get_queryset(self):
        return Reagent.objects.for_tenant(self.request.tenant).select_related(
            'yield_unit'
        ).prefetch_related('items__supply', 'items__unit')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['orders'] = (
            ProductionOrder.objects.for_tenant(self.request.tenant)
            .filter(reagent=self.object)
            .order_by('-created_at')[:20]
        )
        return ctx


class ReagentDeleteView(DeleteView):
    model = Reagent
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:reagent_list')

    def get_queryset(self):
        return Reagent.objects.for_tenant(self.request.tenant)


# ────────────── Ítems de receta ──────────────

@login_required
def reagent_item_add(request, reagent_pk):
    reagent = get_object_or_404(
        Reagent.objects.for_tenant(request.tenant), pk=reagent_pk
    )
    if request.method == 'POST':
        form = ReagentItemForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            form.instance.reagent = reagent
            form.save()
            return redirect('lab_inventory:reagent_detail', pk=reagent.pk)
    else:
        form = ReagentItemForm(tenant=request.tenant)
    return render(request, 'lab_inventory/partials/_form_modal.html', {
        'form': form,
        'title': f'Agregar insumo a {reagent.name}',
    })


@login_required
def reagent_item_delete(request, item_pk):
    item = get_object_or_404(ReagentItem, pk=item_pk)
    reagent_pk = item.reagent.pk
    if request.method == 'POST':
        item.delete()
    return redirect('lab_inventory:reagent_detail', pk=reagent_pk)


# ────────────── Movimientos de stock ──────────────

class StockMovementListView(ListView):
    model = StockMovement
    template_name = 'lab_inventory/movement_list.html'
    context_object_name = 'movements'

    def get_queryset(self):
        qs = (
            StockMovement.objects.for_tenant(self.request.tenant)
            .select_related('supply', 'supplier', 'production_order', 'created_by')
            .order_by('-created_at')
        )
        if q := self.request.GET.get('q'):
            qs = qs.filter(
                Q(supply__name__icontains=q) |
                Q(batch_number__icontains=q) |
                Q(supplier__name__icontains=q)
            )
        if t := self.request.GET.get('type'):
            qs = qs.filter(movement_type=t)
        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_movement_table.html']
        return [self.template_name]


class StockMovementCreateView(CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'lab_inventory/movement_form.html'
    success_url = reverse_lazy('lab_inventory:movement_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['supply'].queryset = Supply.objects.for_tenant(self.request.tenant)
        form.fields['supplier'].queryset = Supplier.objects.for_tenant(self.request.tenant)
        return form


# ────────────── Órdenes de producción ──────────────

class ProductionOrderListView(ListView):
    model = ProductionOrder
    template_name = 'lab_inventory/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        qs = (
            ProductionOrder.objects.for_tenant(self.request.tenant)
            .select_related('reagent', 'created_by')
            .order_by('-created_at')
        )
        if s := self.request.GET.get('status'):
            qs = qs.filter(status=s)
        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_order_table.html']
        return [self.template_name]


class ProductionOrderCreateView(CreateView):
    model = ProductionOrder
    form_class = ProductionOrderForm
    template_name = 'lab_inventory/order_form.html'
    success_url = reverse_lazy('lab_inventory:order_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['reagent'].queryset = Reagent.objects.for_tenant(self.request.tenant)
        return form


class ProductionOrderDetailView(DetailView):
    model = ProductionOrder
    template_name = 'lab_inventory/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return ProductionOrder.objects.for_tenant(self.request.tenant).select_related(
            'reagent', 'created_by'
        ).prefetch_related('reagent__items__supply', 'reagent__items__unit')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['movements'] = (
            StockMovement.objects.for_tenant(self.request.tenant)
            .filter(production_order=self.object)
            .select_related('supply', 'supplier')
        )
        # Calcular insumos necesarios para la orden
        base_yield = self.object.reagent.yield_quantity
        target_qty = self.object.quantity
        factor = target_qty / base_yield if base_yield else Decimal('1')
        needed = []
        for item in self.object.reagent.items.all():
            needed.append({
                'supply': item.supply,
                'required_qty': item.quantity * factor,
                'unit': item.unit,
                'current_stock': item.supply.current_stock,
            })
        ctx['needed_items'] = needed
        return ctx


@login_required
def production_order_start(request, pk):
    """Inicia la orden de producción: consume insumos del inventario."""
    order = get_object_or_404(
        ProductionOrder.objects.for_tenant(request.tenant).select_related(
            'reagent'
        ).prefetch_related('reagent__items__supply'),
        pk=pk,
    )
    if order.status not in ('planned',):
        return redirect('lab_inventory:order_detail', pk=order.pk)

    # Verificar stock suficiente
    base_yield = order.reagent.yield_quantity
    target_qty = order.quantity
    factor = target_qty / base_yield if base_yield else Decimal('1')

    errors = []
    for item in order.reagent.items.all():
        needed = item.quantity * factor
        if item.supply.current_stock < needed:
            errors.append(
                f'Stock insuficiente de {item.supply.name}: '
                f'necesita {needed} {item.unit.abbreviation}, '
                f'disponible {item.supply.current_stock} {item.supply.unit.abbreviation}'
            )

    if errors and request.method == 'GET':
        return render(request, 'lab_inventory/order_detail.html', {
            'order': order,
            'errors': errors,
            'needed_items': [
                {
                    'supply': item.supply,
                    'required_qty': item.quantity * factor,
                    'unit': item.unit,
                    'current_stock': item.supply.current_stock,
                }
                for item in order.reagent.items.all()
            ],
            'movements': StockMovement.objects.for_tenant(request.tenant)
                .filter(production_order=order)
                .select_related('supply'),
        })

    # Consumir insumos
    for item in order.reagent.items.all():
        needed = item.quantity * factor
        StockMovement.objects.create(
            organization=request.tenant,
            supply=item.supply,
            movement_type='exit',
            quantity=needed,
            batch_number=order.batch_number,
            production_order=order,
            reason=f'Consumo OP {order.batch_number} — {order.reagent.name}',
            created_by=request.user,
        )

    order.status = 'in_progress'
    order.started_at = timezone.now()
    order.save()

    return redirect('lab_inventory:order_detail', pk=order.pk)


@login_required
def production_order_complete(request, pk):
    """Completa la orden de producción."""
    order = get_object_or_404(
        ProductionOrder.objects.for_tenant(request.tenant), pk=pk
    )
    if order.status == 'in_progress':
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
    return redirect('lab_inventory:order_detail', pk=order.pk)


@login_required
def production_order_cancel(request, pk):
    """Cancela la orden y revierte los consumos."""
    order = get_object_or_404(
        ProductionOrder.objects.for_tenant(request.tenant), pk=pk
    )
    if order.status in ('planned', 'in_progress'):
        # Revertir consumos si ya se inició
        if order.status == 'in_progress':
            StockMovement.objects.for_tenant(request.tenant).filter(
                production_order=order, movement_type='exit',
            ).delete()
        order.status = 'cancelled'
        order.completed_at = timezone.now()
        order.save()
    return redirect('lab_inventory:order_detail', pk=order.pk)
