from django.shortcuts import redirect
from django.contrib import messages

RUTAS_PUBLICAS = ['/login/', '/logout/', '/password-reset/', '/static/', '/media/', '/__debug__/', '/healthz/']


class TenantMiddleware:
    """Inyecta request.tenant con la organización del usuario logueado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None

        if not request.user.is_authenticated:
            return self.get_response(request)

        if any(request.path.startswith(ruta) for ruta in RUTAS_PUBLICAS):
            return self.get_response(request)

        user = request.user

        if user.is_superadmin or user.is_superuser:
            if user.organization:
                request.tenant = user.organization
            return self.get_response(request)

        if not user.organization:
            messages.error(request, 'Tu cuenta no tiene organización asignada.')
            return redirect('core:login')

        if not user.organization.is_active:
            messages.warning(
                request,
                f'La cuenta de {user.organization.name} está suspendida.'
            )
            return redirect('core:cuenta_suspendida')

        request.tenant = user.organization
        return self.get_response(request)
