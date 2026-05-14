import csv
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView,
)
from apps.core.decorators import role_required
from .models import (
    Category, UnitOfMeasure, Supplier, Supply,
    Reagent, ReagentItem, Batch, ProductionOrder, StockMovement,
)
from .forms import (
    CategoryForm, UnitOfMeasureForm, SupplierForm,
    SupplyForm, ReagentForm, ReagentItemForm,
    BatchForm, ProductionOrderForm, StockMovementForm,
)


# ────────────── Mixins de permisos ──────────────

class StaffOrAboveMixin:
    """Permite acceso a staff, manager, admin y superadmin."""
    @method_decorator(role_required('admin', 'manager', 'staff'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class AdminOrAboveMixin:
    """Solo admin, manager y superadmin pueden crear/editar/eliminar."""
    @method_decorator(role_required('admin', 'manager'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class AuditUpdateMixin:
    """Registra quién modificó el registro."""
    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        return super().form_valid(form)


# ────────────── Dashboard ──────────────

@login_required
@role_required('admin', 'manager', 'staff')
def dashboard(request):
    tenant = request.tenant
    reagents = Reagent.objects.for_tenant(tenant)
    orders = ProductionOrder.objects.for_tenant(tenant)

    # Optimizado: calcular stock con annotate en lugar de N+1
    supplies_with_stock = (
        Supply.objects.for_tenant(tenant)
        .select_related('category', 'unit')
        .annotate(computed_stock=Sum('movements__quantity'))
    )

    total_supplies = supplies_with_stock.count()
    total_reagents = reagents.count()

    # Calcular low stock sin N+1
    low_stock_items = []
    for s in supplies_with_stock:
        stock = s.computed_stock or Decimal('0')
        if stock <= s.stock_min:
            s._current_stock = stock
            low_stock_items.append(s)

    # Reagent stock alerts
    reagent_low_stock = []
    for r in reagents.select_related('yield_unit'):
        if r.stock_status == 'low':
            r._current_stock = r.current_stock
            reagent_low_stock.append(r)

    pending_orders = orders.filter(status='planned').count()
    in_progress_orders = orders.filter(status='in_progress').count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    recent_movements = (
        StockMovement.objects.for_tenant(tenant)
        .select_related('supply', 'reagent', 'created_by')[:10]
    )

    # Lotes próximos a vencer (30 días)
    from datetime import date, timedelta
    expiring_batches = (
        Batch.objects.for_tenant(tenant)
        .select_related('supply', 'reagent')
        .filter(
            expiration_date__gte=date.today(),
            expiration_date__lte=date.today() + timedelta(days=30),
        )
        .order_by('expiration_date')[:10]
    )

    ctx = {
        'total_supplies': total_supplies,
        'total_reagents': total_reagents,
        'low_stock_count': len(low_stock_items),
        'low_stock_items': low_stock_items,
        'reagent_low_stock': reagent_low_stock,
        'expiring_batches': expiring_batches,
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'recent_movements': recent_movements,
    }
    return render(request, 'lab_inventory/dashboard.html', ctx)


# ────────────── Categorías ──────────────

class CategoryListView(StaffOrAboveMixin, ListView):
    model = Category
    template_name = 'lab_inventory/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.for_tenant(self.request.tenant)

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_category_table.html']
        return [self.template_name]


class CategoryCreateView(AdminOrAboveMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:category_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)


class CategoryUpdateView(AuditUpdateMixin, AdminOrAboveMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:category_list')

    def get_queryset(self):
        return Category.objects.for_tenant(self.request.tenant)


class CategoryDeleteView(AdminOrAboveMixin, DeleteView):
    model = Category
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:category_list')

    def get_queryset(self):
        return Category.objects.for_tenant(self.request.tenant)


# ────────────── Unidades de medida ──────────────

class UOMListView(StaffOrAboveMixin, ListView):
    model = UnitOfMeasure
    template_name = 'lab_inventory/uom_list.html'
    context_object_name = 'uoms'

    def get_queryset(self):
        return UnitOfMeasure.objects.for_tenant(self.request.tenant)

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_uom_table.html']
        return [self.template_name]


class UOMCreateView(AdminOrAboveMixin, CreateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:uom_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)


class UOMUpdateView(AuditUpdateMixin, AdminOrAboveMixin, UpdateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'lab_inventory/partials/_form_modal.html'
    success_url = reverse_lazy('lab_inventory:uom_list')

    def get_queryset(self):
        return UnitOfMeasure.objects.for_tenant(self.request.tenant)


class UOMDeleteView(AdminOrAboveMixin, DeleteView):
    model = UnitOfMeasure
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:uom_list')

    def get_queryset(self):
        return UnitOfMeasure.objects.for_tenant(self.request.tenant)


# ────────────── Proveedores ──────────────

class SupplierListView(StaffOrAboveMixin, ListView):
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


class SupplierCreateView(AdminOrAboveMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'lab_inventory/supplier_form.html'
    success_url = reverse_lazy('lab_inventory:supplier_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)


class SupplierUpdateView(AuditUpdateMixin, AdminOrAboveMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'lab_inventory/supplier_form.html'
    success_url = reverse_lazy('lab_inventory:supplier_list')

    def get_queryset(self):
        return Supplier.objects.for_tenant(self.request.tenant)


class SupplierDeleteView(AdminOrAboveMixin, DeleteView):
    model = Supplier
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:supplier_list')

    def get_queryset(self):
        return Supplier.objects.for_tenant(self.request.tenant)


# ────────────── Insumos ──────────────

class SupplyListView(StaffOrAboveMixin, ListView):
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


class SupplyCreateView(AdminOrAboveMixin, CreateView):
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


class SupplyUpdateView(AuditUpdateMixin, AdminOrAboveMixin, UpdateView):
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


class SupplyDetailView(StaffOrAboveMixin, DetailView):
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


class SupplyDeleteView(AdminOrAboveMixin, DeleteView):
    model = Supply
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:supply_list')

    def get_queryset(self):
        return Supply.objects.for_tenant(self.request.tenant)


# ────────────── Reactivos ──────────────

class ReagentListView(StaffOrAboveMixin, ListView):
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


class ReagentCreateView(AdminOrAboveMixin, CreateView):
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


class ReagentUpdateView(AuditUpdateMixin, AdminOrAboveMixin, UpdateView):
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


class ReagentDetailView(StaffOrAboveMixin, DetailView):
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


class ReagentDeleteView(AdminOrAboveMixin, DeleteView):
    model = Reagent
    template_name = 'lab_inventory/partials/_confirm_delete.html'
    success_url = reverse_lazy('lab_inventory:reagent_list')

    def get_queryset(self):
        return Reagent.objects.for_tenant(self.request.tenant)


# ────────────── Ítems de receta ──────────────

@login_required
@role_required('admin', 'manager')
def reagent_item_add(request, reagent_pk):
    reagent = get_object_or_404(
        Reagent.objects.for_tenant(request.tenant), pk=reagent_pk
    )
    if request.method == 'POST':
        form = ReagentItemForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            form.instance.reagent = reagent
            form.instance.organization = request.tenant
            form.save()
            return redirect('lab_inventory:reagent_detail', pk=reagent.pk)
    else:
        form = ReagentItemForm(tenant=request.tenant)
    return render(request, 'lab_inventory/partials/_form_modal.html', {
        'form': form,
        'title': f'Agregar insumo a {reagent.name}',
    })


@login_required
@role_required('admin', 'manager')
def reagent_item_delete(request, item_pk):
    item = get_object_or_404(
        ReagentItem.objects.for_tenant(request.tenant), pk=item_pk
    )
    reagent_pk = item.reagent.pk
    if request.method == 'POST':
        item.delete()
    return redirect('lab_inventory:reagent_detail', pk=reagent_pk)


# ────────────── Lotes ──────────────

class BatchListView(StaffOrAboveMixin, ListView):
    model = Batch
    template_name = 'lab_inventory/batch_list.html'
    context_object_name = 'batches'

    def get_queryset(self):
        qs = (
            Batch.objects.for_tenant(self.request.tenant)
            .select_related('supply', 'reagent', 'supplier')
        )
        if q := self.request.GET.get('q'):
            qs = qs.filter(
                Q(batch_number__icontains=q) |
                Q(supply__name__icontains=q) |
                Q(reagent__name__icontains=q)
            )
        if self.request.GET.get('expired') == '1':
            from datetime import date
            qs = qs.filter(expiration_date__lt=date.today())
        if self.request.GET.get('expiring') == '1':
            from datetime import date, timedelta
            qs = qs.filter(
                expiration_date__gte=date.today(),
                expiration_date__lte=date.today() + timedelta(days=30),
            )
        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ['lab_inventory/partials/_batch_table.html']
        return [self.template_name]


class BatchCreateView(AdminOrAboveMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'lab_inventory/batch_form.html'
    success_url = reverse_lazy('lab_inventory:batch_list')

    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['supply'].queryset = Supply.objects.for_tenant(self.request.tenant)
        form.fields['supplier'].queryset = Supplier.objects.for_tenant(self.request.tenant).filter(is_active=True)
        return form


# ────────────── Movimientos de stock ──────────────

class StockMovementListView(StaffOrAboveMixin, ListView):
    model = StockMovement
    template_name = 'lab_inventory/movement_list.html'
    context_object_name = 'movements'

    def get_queryset(self):
        qs = (
            StockMovement.objects.for_tenant(self.request.tenant)
            .select_related('supply', 'reagent', 'supplier', 'production_order', 'created_by')
            .order_by('-created_at')
        )
        if q := self.request.GET.get('q'):
            qs = qs.filter(
                Q(supply__name__icontains=q) |
                Q(reagent__name__icontains=q) |
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


class StockMovementCreateView(AdminOrAboveMixin, CreateView):
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
        form.fields['supplier'].queryset = Supplier.objects.for_tenant(self.request.tenant).filter(is_active=True)
        form.fields['production_order'].queryset = ProductionOrder.objects.for_tenant(self.request.tenant)
        return form


# ────────────── Órdenes de producción ──────────────

class ProductionOrderListView(StaffOrAboveMixin, ListView):
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


class ProductionOrderCreateView(AdminOrAboveMixin, CreateView):
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


class ProductionOrderDetailView(StaffOrAboveMixin, DetailView):
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
            .select_related('supply', 'reagent', 'supplier')
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
@role_required('admin', 'manager')
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
    order.updated_by = request.user
    order.save()

    return redirect('lab_inventory:order_detail', pk=order.pk)


@login_required
@role_required('admin', 'manager')
def production_order_complete(request, pk):
    """Completa la orden de producción y registra entrada del reactivo producido."""
    order = get_object_or_404(
        ProductionOrder.objects.for_tenant(request.tenant).select_related('reagent'),
        pk=pk,
    )
    if order.status == 'in_progress':
        # Crear lote del reactivo producido
        batch = Batch.objects.create(
            organization=request.tenant,
            reagent=order.reagent,
            batch_number=order.batch_number,
        )
        # Registrar entrada de stock del reactivo
        StockMovement.objects.create(
            organization=request.tenant,
            reagent=order.reagent,
            movement_type='entry',
            quantity=order.quantity,
            batch=batch,
            batch_number=order.batch_number,
            production_order=order,
            reason=f'Producción completada OP {order.batch_number}',
            created_by=request.user,
        )
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.updated_by = request.user
        order.save()
    return redirect('lab_inventory:order_detail', pk=order.pk)


@login_required
@role_required('admin', 'manager')
def production_order_cancel(request, pk):
    """Cancela la orden y revierte los consumos con movimientos de entrada."""
    order = get_object_or_404(
        ProductionOrder.objects.for_tenant(request.tenant), pk=pk
    )
    if order.status in ('planned', 'in_progress'):
        # Revertir consumos creando entradas compensatorias (auditoría limpia)
        if order.status == 'in_progress':
            exit_movements = StockMovement.objects.for_tenant(request.tenant).filter(
                production_order=order, movement_type='exit',
            )
            for mov in exit_movements:
                StockMovement.objects.create(
                    organization=request.tenant,
                    supply=mov.supply,
                    movement_type='entry',
                    quantity=abs(mov.quantity),
                    batch_number=mov.batch_number,
                    production_order=order,
                    reason=f'Reversión por cancelación OP {order.batch_number}',
                    created_by=request.user,
                )
        order.status = 'cancelled'
        order.completed_at = timezone.now()
        order.updated_by = request.user
        order.save()
    return redirect('lab_inventory:order_detail', pk=order.pk)


# ────────────── Exportaciones CSV ──────────────

@login_required
@role_required('admin', 'manager')
def export_supplies_csv(request):
    """Exporta insumos con stock actual a CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="insumos.csv"'
    writer = csv.writer(response)
    writer.writerow(['Código', 'Nombre', 'Categoría', 'Unidad', 'Stock actual', 'Stock mín', 'Stock máx', 'Estado', 'Activo'])
    for s in Supply.objects.for_tenant(request.tenant).select_related('category', 'unit'):
        writer.writerow([
            s.code, s.name, s.category.name, s.unit.abbreviation,
            s.current_stock, s.stock_min, s.stock_max,
            s.stock_status, 'Sí' if s.is_active else 'No',
        ])
    return response


@login_required
@role_required('admin', 'manager')
def export_movements_csv(request):
    """Exporta movimientos de stock a CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="movimientos.csv"'
    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Insumo/Reactivo', 'Tipo', 'Cantidad', 'Lote', 'Proveedor', 'Motivo', 'Registrado por'])
    for m in StockMovement.objects.for_tenant(request.tenant).select_related('supply', 'reagent', 'supplier', 'created_by').order_by('-created_at'):
        item_name = m.supply.name if m.supply else (m.reagent.name if m.reagent else '')
        writer.writerow([
            m.created_at.strftime('%Y-%m-%d %H:%M'),
            item_name, m.get_movement_type_display(), m.quantity,
            m.batch_number, m.supplier.name if m.supplier else '',
            m.reason, str(m.created_by) if m.created_by else '',
        ])
    return response


@login_required
@role_required('admin', 'manager')
def export_orders_csv(request):
    """Exporta órdenes de producción a CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ordenes.csv"'
    writer = csv.writer(response)
    writer.writerow(['Lote', 'Reactivo', 'Cantidad', 'Estado', 'Creado por', 'Creado', 'Iniciado', 'Completado'])
    for o in ProductionOrder.objects.for_tenant(request.tenant).select_related('reagent', 'created_by').order_by('-created_at'):
        writer.writerow([
            o.batch_number, o.reagent.name, o.quantity,
            o.get_status_display(), str(o.created_by) if o.created_by else '',
            o.created_at.strftime('%Y-%m-%d %H:%M'),
            o.started_at.strftime('%Y-%m-%d %H:%M') if o.started_at else '',
            o.completed_at.strftime('%Y-%m-%d %H:%M') if o.completed_at else '',
        ])
    return response


@login_required
@role_required('admin', 'manager')
def export_batches_csv(request):
    """Exporta lotes a CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lotes.csv"'
    writer = csv.writer(response)
    writer.writerow(['Lote', 'Tipo', 'Insumo/Reactivo', 'Vencimiento', 'Proveedor', 'Stock lote', 'Notas'])
    for b in Batch.objects.for_tenant(request.tenant).select_related('supply', 'reagent', 'supplier').order_by('-created_at'):
        writer.writerow([
            b.batch_number, 'Insumo' if b.supply else 'Reactivo',
            b.item.name if b.item else '',
            b.expiration_date.strftime('%Y-%m-%d') if b.expiration_date else '',
            b.supplier.name if b.supplier else '',
            b.current_stock, b.notes,
        ])
    return response
