from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """Restringe acceso a roles específicos. Superadmin siempre tiene acceso."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_superadmin', False):
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles:
                messages.error(request, 'No tienes permiso para acceder a esta sección.')
                return redirect('core:login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def superadmin_required(view_func):
    """Solo el superadmin puede acceder."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.is_superadmin and not request.user.is_superuser:
            messages.error(request, 'Acceso restringido.')
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_required(view_func):
    """Garantiza que request.tenant existe antes de entrar a la vista."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not getattr(request, 'tenant', None) and not request.user.is_superadmin:
            messages.error(request, 'Sin organización asignada.')
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper
