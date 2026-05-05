from django.urls import path
from . import views

app_name = 'lab_inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Categorías
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<uuid:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<uuid:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Unidades de medida
    path('uoms/', views.UOMListView.as_view(), name='uom_list'),
    path('uoms/new/', views.UOMCreateView.as_view(), name='uom_create'),
    path('uoms/<uuid:pk>/edit/', views.UOMUpdateView.as_view(), name='uom_update'),
    path('uoms/<uuid:pk>/delete/', views.UOMDeleteView.as_view(), name='uom_delete'),

    # Proveedores
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/new/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<uuid:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<uuid:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),

    # Insumos
    path('supplies/', views.SupplyListView.as_view(), name='supply_list'),
    path('supplies/new/', views.SupplyCreateView.as_view(), name='supply_create'),
    path('supplies/<uuid:pk>/', views.SupplyDetailView.as_view(), name='supply_detail'),
    path('supplies/<uuid:pk>/edit/', views.SupplyUpdateView.as_view(), name='supply_update'),
    path('supplies/<uuid:pk>/delete/', views.SupplyDeleteView.as_view(), name='supply_delete'),

    # Reactivos
    path('reagents/', views.ReagentListView.as_view(), name='reagent_list'),
    path('reagents/new/', views.ReagentCreateView.as_view(), name='reagent_create'),
    path('reagents/<uuid:pk>/', views.ReagentDetailView.as_view(), name='reagent_detail'),
    path('reagents/<uuid:pk>/edit/', views.ReagentUpdateView.as_view(), name='reagent_update'),
    path('reagents/<uuid:pk>/delete/', views.ReagentDeleteView.as_view(), name='reagent_delete'),
    path('reagents/<uuid:reagent_pk>/items/add/', views.reagent_item_add, name='reagent_item_add'),
    path('reagents/items/<uuid:item_pk>/delete/', views.reagent_item_delete, name='reagent_item_delete'),

    # Movimientos de stock
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/new/', views.StockMovementCreateView.as_view(), name='movement_create'),

    # Órdenes de producción
    path('orders/', views.ProductionOrderListView.as_view(), name='order_list'),
    path('orders/new/', views.ProductionOrderCreateView.as_view(), name='order_create'),
    path('orders/<uuid:pk>/', views.ProductionOrderDetailView.as_view(), name='order_detail'),
    path('orders/<uuid:pk>/start/', views.production_order_start, name='order_start'),
    path('orders/<uuid:pk>/complete/', views.production_order_complete, name='order_complete'),
    path('orders/<uuid:pk>/cancel/', views.production_order_cancel, name='order_cancel'),
]
