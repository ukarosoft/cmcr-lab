from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Administración de organizaciones (tenants)."""
    list_display = ['name', 'slug', 'plan', 'is_active', 'total_usuarios', 'created_at']
    list_filter = ['plan', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administración de usuarios con soporte multi-tenant.
    Un admin solo ve usuarios de su propia organización.
    Un superadmin ve todos los usuarios.
    """
    list_display = ['username', 'get_full_name', 'role', 'organization', 'is_active']
    list_filter = ['role', 'is_active', 'organization']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    readonly_fields = ['id']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Ukarasoft', {'fields': ('organization', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Ukarasoft', {'fields': ('organization', 'role')}),
    )

    def get_queryset(self, request):
        """Filtra usuarios por organización para admins no-super."""
        qs = super().get_queryset(request)
        if request.user.is_superuser or getattr(request.user, 'is_superadmin', False):
            return qs
        if request.user.organization:
            return qs.filter(organization=request.user.organization)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        """Solo puede editar usuarios de su org."""
        if not super().has_change_permission(request, obj):
            return False
        if obj is None:
            return True
        if request.user.is_superuser or getattr(request.user, 'is_superadmin', False):
            return True
        return obj.organization == request.user.organization
