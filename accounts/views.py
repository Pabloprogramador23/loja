from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST


def criar_loja_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    from .forms import StoreRegistrationForm
    from core.models import Store

    if request.method == 'POST':
        form = StoreRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                Store.objects.create(
                    name=form.cleaned_data['store_name'],
                    subdomain=form.cleaned_data['subdomain'],
                    owner=user,
                    is_active=True,
                )
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
    else:
        form = StoreRegistrationForm()

    return render(request, 'accounts/criar_loja.html', {'form': form})


def signup_view(request):
    from .forms import CustomerSignupForm
    if request.method == 'POST':
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('index')
    else:
        form = CustomerSignupForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if getattr(user, 'owned_store', None):
                return redirect('dashboard')
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('index')
    return redirect('index')


def auth_modal_view(request):
    if request.user.is_authenticated:
        return HttpResponse('<script>window.location.href="/checkout/";</script>')
    return render(request, 'accounts/auth_modal.html')


@require_POST
def checkout_login_view(request):
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    user = authenticate(request, username=email, password=password)
    if user is not None:
        auth_login(request, user)
        return HttpResponse('<script>window.location.href="/checkout/";</script>')
    return render(request, 'accounts/partials/modal_login.html', {
        'error': 'E-mail ou senha incorretos.',
    })


@require_POST
def checkout_signup_view(request):
    from .forms import CheckoutSignupForm
    from core.models import UserProfile
    form = CheckoutSignupForm(request.POST)
    if form.is_valid():
        user = form.save()
        phone = form.cleaned_data.get('phone', '')
        if phone:
            UserProfile.objects.update_or_create(user=user, defaults={'phone': phone})
        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return HttpResponse('<script>window.location.href="/checkout/";</script>')
    return render(request, 'accounts/partials/modal_signup.html', {
        'form': form,
    })
