from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme



def login_view(request):
    """Vista de inicio de sesión."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Validar next_url para prevenir open redirect
            next_url = request.POST.get('next') or request.GET.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return HttpResponseRedirect(next_url)
            return redirect('core:dashboard')
        else:
            error = 'Usuario o contraseña incorrectos.'

    return render(request, 'core/login.html', {
        'error': error,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    """Vista de cierre de sesión."""
    logout(request)
    return redirect('core:login')


@login_required
def dashboard_view(request):
    """Redirige al dashboard de inventario."""
    return redirect('lab_inventory:dashboard')


def cuenta_suspendida_view(request):
    """Vista para cuentas suspendidas."""
    return render(request, 'core/cuenta_suspendida.html', status=403)


def healthz(request):
    """Endpoint público para healthcheck (Docker, load balancers)."""
    return JsonResponse({'status': 'ok'})


def csrf_failure(request, reason=''):
    """Vista personalizada para fallos CSRF — reemplaza la página genérica de Django."""
    return render(request, 'core/csrf_failure.html', {
        'reason': reason,
    }, status=403)
