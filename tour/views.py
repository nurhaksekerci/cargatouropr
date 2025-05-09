from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
import re
import requests
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import (
    Operation, Operationday, Operationitem, Sirket, Tour, Transfer, Vehicle, Guide, Hotel,
    Activity, Museum, Supplier, Activitysupplier,
    Cost, Activitycost, Buyercompany, Personel, UserActivityLog
)
from .forms import (
    OperationFileForm, OperationForm, OperationItemForm, SirketForm, TourForm, TransferForm, VehicleForm, GuideForm, HotelForm,
    ActivityForm, MuseumForm, SupplierForm, ActivitysupplierForm,
    CostForm, ActivitycostForm, BuyercompanyForm, PersonelForm,

)
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.template.defaulttags import register

# Create your views here.

def login_view(request):
    """
    Kullanıcı giriş işlemi için view fonksiyonu.

    Args:
        request: Django HTTP request

    Returns:
        Başarılı girişte ana sayfaya, başarısız girişte login sayfasına yönlendirir
    """
    # Kullanıcı zaten giriş yapmışsa ana sayfaya yönlendir
    if request.user.is_authenticated:
        return redirect('tour:dashboard')

    # Form gönderildiğinde
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Kullanıcı adı ve şifre kontrolü
        if username and password:
            user = authenticate(request, username=username, password=password)

            # Giriş başarılıysa
            if user is not None:
                login(request, user)

                # Kullanıcı bir şirketle ilişkilendirilmiş mi kontrol et
                company = None
                if hasattr(user, 'personel') and user.personel.exists():
                    personel = user.personel.first()
                    company = personel.company
                    messages.success(request, f"HOŞGELDİNİZ, {user.get_full_name().upper()}")

                    # Kullanıcı giriş logunu oluştur
                    UserActivityLog.objects.create(
                        company=company,
                        staff=personel,
                        action=f"Kullanıcı giriş yaptı: {user.username}",
                        ip_address=get_client_ip(request),
                        browser_info=request.META.get('HTTP_USER_AGENT', '')
                    )
                elif user.is_superuser:
                    messages.success(request, f"HOŞGELDİNİZ, {user.get_full_name().upper()}")

                    # Süper kullanıcı giriş logunu oluştur
                    UserActivityLog.objects.create(
                        action=f"Süper kullanıcı giriş yaptı: {user.username}",
                        ip_address=get_client_ip(request),
                        browser_info=request.META.get('HTTP_USER_AGENT', '')
                    )
                else:
                    messages.warning(request, "HESABINIZ HERHANGİ BİR ŞİRKETLE İLİŞKİLENDİRİLMEMİŞ!")

                # Kullanıcı daha önce bir sayfaya erişmeye çalışmışsa oraya yönlendir
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)

                # Varsayılan olarak ana sayfaya yönlendir
                return redirect('tour:dashboard')
            else:
                messages.error(request, "KULLANICI ADI VEYA ŞİFRE YANLIŞ!")
        else:
            messages.error(request, "LÜTFEN KULLANICI ADI VE ŞİFRE GİRİNİZ!")

    return render(request, 'login.html')

def logout_view(request):
    """
    Kullanıcı çıkış işlemi için view fonksiyonu.

    Args:
        request: Django HTTP request

    Returns:
        Çıkış sonrası login sayfasına yönlendirir
    """
    # Çıkış yapmadan önce log kaydı oluştur
    if request.user.is_authenticated:
        company = None
        staff = None

        if hasattr(request.user, 'personel') and request.user.personel.exists():
            staff = request.user.personel.first()
            company = staff.company

            # Personel için logout logu
            UserActivityLog.objects.create(
                company=company,
                staff=staff,
                action=f"Kullanıcı çıkış yaptı: {request.user.username}",
                ip_address=get_client_ip(request),
                browser_info=request.META.get('HTTP_USER_AGENT', '')
            )
        elif request.user.is_superuser:
            # Süper kullanıcı için logout logu
            UserActivityLog.objects.create(
                action=f"Süper kullanıcı çıkış yaptı: {request.user.username}",
                ip_address=get_client_ip(request),
                browser_info=request.META.get('HTTP_USER_AGENT', '')
            )

    logout(request)
    messages.success(request, "BAŞARIYLA ÇIKIŞ YAPTINIZ!")
    return redirect('tour:login')

@login_required(login_url='tour:login')
def dashboard(request):
    """
    Kullanıcı dashboard sayfası için view fonksiyonu.
    Performans için cache kullanır ve veritabanı sorgularını optimize eder.

    Args:
        request: Django HTTP request

    Returns:
        Dashboard sayfasını render eder
    """
    # Cache anahtarı oluştur
    cache_key = f"dashboard_{request.user.id}"
    cache_timeout = 300  # 5 dakika

    # Cache'den veriyi almaya çalış
    cached_data = cache.get(cache_key)
    if cached_data:
        return render(request, 'dashboard.html', cached_data)

    # Kullanıcı ve şirket bilgilerini al
    company = None
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        personel = request.user.personel.first()
        company = personel.company

    # Model listesi ve ilgili filtreler
    models = {
        'tours': Tour,
        'transfers': Transfer,
        'vehicles': Vehicle,
        'guides': Guide,
        'hotels': Hotel,
        'suppliers': Supplier,
        'activities': Activity,
        'activitysuppliers': Activitysupplier,
        'buyercompanies': Buyercompany
    }

    # Temel context
    context = {
        'user': request.user,
        'company': company,
    }

    # Her model için aktif ve silinmiş kayıt sayılarını hesapla
    for model_name, model in models.items():
        # Aktif kayıtlar için sorgu
        active_query = model.objects.filter(is_delete=False)
        # Silinmiş kayıtlar için sorgu
        deleted_query = model.objects.filter(is_delete=True)

        # Eğer kullanıcı bir şirkete bağlıysa, şirket filtresini ekle
        if company and not request.user.is_superuser:
            active_query = active_query.filter(company=company)
            deleted_query = deleted_query.filter(company=company)

        # Sayıları hesapla ve context'e ekle
        context[f'{model_name}_count'] = active_query.count()
        context[f'deleted_{model_name}_count'] = deleted_query.count()

    # Son aktivite loglarını al (son 5 kayıt)
    if company and not request.user.is_superuser:
        recent_logs = UserActivityLog.objects.filter(
            company=company,
            staff=personel
        ).order_by('-timestamp')[:5]
    else:
        recent_logs = UserActivityLog.objects.all().order_by('-timestamp')[:5]

    context['recent_logs'] = recent_logs

    # Aktif operasyonları al
    today = timezone.now().date()
    if company and not request.user.is_superuser:
        staff = request.user.personel.first()
        active_operations = Operation.objects.filter(
            company=company,
            is_delete=False,
            start__lte=today,
            finish__gte=today,
            follow_staff=staff
        ).select_related('buyer_company', 'follow_staff')
    else:
        active_operations = None

    context['active_operations'] = active_operations

    # Bugünün iş listesini al
    if company and not request.user.is_superuser:
        staff = request.user.personel.first()
        today_jobs = Operationitem.objects.filter(
            company=company,
            day__date=today,
            day__operation__follow_staff=staff
        ).select_related(
            'day',
            'day__operation',
            'tour',
            'transfer',
            'vehicle',
            'supplier',
            'hotel',
            'activity',
            'guide'
        )
    else:
        today_jobs = None

    context['today_jobs'] = today_jobs

    # Log kaydı oluştur
    if company and not request.user.is_superuser:
        UserActivityLog.objects.create(
            company=company,
            staff=personel,
            action="Dashboard sayfasını ziyaret etti",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )
    else:
        UserActivityLog.objects.create(
            action="Süper kullanıcı dashboard sayfasını ziyaret etti",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )

    # Context'i cache'e ekle
    cache.set(cache_key, context, cache_timeout)
    return render(request, 'dashboard.html', context)

@login_required(login_url='tour:login')
def generic_list(request, model_name):
    """
    Generic view function that lists objects from a specified model.
    Optimized for faster loading with database query optimization.

    Args:
        request: Django HTTP request
        model_name: String name of the model to list objects from

    Returns:
        Rendered template with model objects
    """
    # Model adı ve model sınıfı eşleştirmesi
    model_map = {
        'sirket': Sirket,
        'tour': Tour,
        'transfer': Transfer,
        'vehicle': Vehicle,
        'guide': Guide,
        'hotel': Hotel,
        'activity': Activity,
        'museum': Museum,
        'supplier': Supplier,
        'activitysupplier': Activitysupplier,
        'cost': Cost,
        'activitycost': Activitycost,
        'buyercompany': Buyercompany,
        'personel': Personel,
    }

    # Model adını kontrol et
    if model_name.lower() not in model_map:
        raise Http404(f"Model '{model_name}' bulunamadı")

    # Model sınıfını al
    model = model_map[model_name.lower()]

    # Arama sorgusu
    query = request.GET.get('q')

    # Cache anahtarı oluştur - kullanıcı ve model adına göre
    cache_key = f"generic_list_{model_name}_{request.user.id}"
    cache_timeout = 180  # 3 dakika

    # Eğer arama yapılmıyorsa cache'den veri getirmeyi dene
    if not query:
        cached_data = cache.get(cache_key)
        if cached_data:
            # Log kaydı oluştur
            _create_list_view_log(request, model._meta)
            return render(request, 'generic/list.html', cached_data)

    # Modele özgü select_related ve prefetch_related ayarları
    select_related_fields = []
    prefetch_related_fields = []

    # Model bazlı ilişkileri belirle
    if model_name == 'tour' or model_name == 'transfer' or model_name == 'vehicle' or \
       model_name == 'activity' or model_name == 'museum' or model_name == 'supplier' or \
       model_name == 'activitysupplier' or model_name == 'buyercompany' or model_name == 'personel':
        select_related_fields.append('company')

    if model_name == 'personel':
        select_related_fields.append('user')

    if model_name == 'cost':
        select_related_fields.extend(['company', 'supplier', 'tour', 'transfer'])

    if model_name == 'activitycost':
        select_related_fields.extend(['company', 'supplier', 'activity'])

    # QuerySet oluştur ve ilişkili alanları ekle
    base_queryset = model.objects.filter(is_delete=False)

    # select_related ekle (foreign keys)
    if select_related_fields:
        base_queryset = base_queryset.select_related(*select_related_fields)

    # prefetch_related ekle (many-to-many veya reverse relations)
    if prefetch_related_fields:
        base_queryset = base_queryset.prefetch_related(*prefetch_related_fields)

    # Eğer kullanıcı bir şirket personeli ise, sadece kendi şirketinin verilerini göster
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        personel = request.user.personel.first()
        company = personel.company
        queryset = base_queryset.filter(company=company)
    else:
        # Admin için tüm kayıtları getir
        queryset = base_queryset

    # Arama işlemi
    if query:
        # Model alanlarını al
        search_fields = []
        for field in model._meta.fields:
            # Sadece metin tabanlı alanları ekle
            if field.get_internal_type() in ['CharField', 'TextField']:
                search_fields.append(field.name)

        # Dinamik Q nesnesi oluştur
        if search_fields:
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})

            queryset = queryset.filter(q_objects)

    # Veritabanından veriyi al (deferred loading kullanma)
    objects = list(queryset)

    # Şablona göndereceğimiz context
    context = {
        'objects': objects,
        'model_name': model_name,
        'model_verbose_name': model._meta.verbose_name,
        'model_verbose_name_plural': model._meta.verbose_name_plural,
        'query': query,  # Arama sorgusunu context'e ekle
    }

    # Log kaydı oluştur
    _create_list_view_log(request, model._meta)

    # Önbelleğe al (sadece arama yapılmıyorsa)
    if not query:
        cache.set(cache_key, context, cache_timeout)

    # Generic template kullan
    return render(request, 'generic/list.html', context)

def _create_list_view_log(request, model_meta):
    """
    Liste görüntüleme logları için yardımcı fonksiyon
    """
    company = None
    staff = None

    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company

        # Personel için log kaydı
        UserActivityLog.objects.create(
            company=company,
            staff=staff,
            action=f"{model_meta.verbose_name_plural} listesini ziyaret etti",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )
    elif request.user.is_superuser:
        # Süper kullanıcı için log kaydı
        UserActivityLog.objects.create(
            action=f"Süper kullanıcı {model_meta.verbose_name_plural} listesini ziyaret etti",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )

@login_required(login_url='tour:login')
def generic_create(request, model_name):
    """
    Generic view function for creating objects of a specified model.

    Args:
        request: Django HTTP request
        model_name: String name of the model to create an object for

    Returns:
        Rendered form template or redirect to list view on success
    """
    # Form sınıfı eşleştirmesi
    form_map = {
        'sirket': SirketForm,
        'tour': TourForm,
        'transfer': TransferForm,
        'vehicle': VehicleForm,
        'guide': GuideForm,
        'hotel': HotelForm,
        'activity': ActivityForm,
        'museum': MuseumForm,
        'supplier': SupplierForm,
        'activitysupplier': ActivitysupplierForm,
        'cost': CostForm,
        'activitycost': ActivitycostForm,
        'buyercompany': BuyercompanyForm,
        'personel': PersonelForm,
    }

    # Model sınıfı eşleştirmesi
    model_map = {
        'sirket': Sirket,
        'tour': Tour,
        'transfer': Transfer,
        'vehicle': Vehicle,
        'guide': Guide,
        'hotel': Hotel,
        'activity': Activity,
        'museum': Museum,
        'supplier': Supplier,
        'activitysupplier': Activitysupplier,
        'cost': Cost,
        'activitycost': Activitycost,
        'buyercompany': Buyercompany,
        'personel': Personel,
    }

    # Model adını kontrol et
    if model_name.lower() not in form_map:
        raise Http404(f"Model '{model_name}' bulunamadı")

    # Form ve model sınıflarını al
    FormClass = form_map[model_name.lower()]
    Model = model_map[model_name.lower()]

    # Kullanıcı şirket bilgisi al
    company = None
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        if request.user.personel.first().company:
            company = request.user.personel.first().company
    elif request.user.is_superuser:
        company = Sirket.objects.get(id=1)

    # POST isteği ise formu işle
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            # Personel formu özel işlem gerektiriyor
            if model_name.lower() == 'personel':
                instance = form.save(commit=True, company=company)
            else:
                instance = form.save(commit=False)
                # Şirket bilgisi gerekiyorsa ve kullanıcı bir şirkete bağlıysa
                if hasattr(Model, 'company') and company:
                    instance.company = company
                instance.save()

            # Kayıt oluşturma log kaydını ekle
            staff = None
            if hasattr(request.user, 'personel') and request.user.personel.exists():
                staff = request.user.personel.first()

                # Personel için log kaydı
                log_action = f"{Model._meta.verbose_name} oluşturdu. Detaylar: "

                # Model alanlarına göre detay bilgileri ekle
                for field in Model._meta.fields:
                    if field.name not in ['id', 'created_at', 'updated_at', 'is_delete']:
                        field_value = getattr(instance, field.name)
                        if field_value is not None:
                            log_action += f"{field.verbose_name}: {field_value}, "

                # Son virgülü kaldır
                log_action = log_action.rstrip(', ')

                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=log_action,
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
            elif request.user.is_superuser:
                # Süper kullanıcı için log kaydı
                log_action = f"Süper kullanıcı {Model._meta.verbose_name} oluşturdu. Detaylar: "

                # Model alanlarına göre detay bilgileri ekle
                for field in Model._meta.fields:
                    if field.name not in ['id', 'created_at', 'updated_at', 'is_delete']:
                        field_value = getattr(instance, field.name)
                        if field_value is not None:
                            log_action += f"{field.verbose_name}: {field_value}, "

                # Son virgülü kaldır
                log_action = log_action.rstrip(', ')

                UserActivityLog.objects.create(
                    action=log_action,
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )

            # Başarı mesajı
            messages.success(
                request,
                f"{Model._meta.verbose_name} başarıyla oluşturuldu."
            )

            # Liste sayfasına yönlendir
            return redirect('tour:' + model_name.lower() + '_list')
    else:
        # GET isteği ise boş form görüntüle
        form = FormClass()

    # Şablona göndereceğimiz context
    context = {
        'form': form,
        'model_name': model_name,
        'model_verbose_name': Model._meta.verbose_name,
        'form_action': 'Oluştur',
        'is_create': True
    }

    # Generic template kullan
    return render(request, 'generic/form.html', context)

@login_required(login_url='tour:login')
def generic_update(request, model_name, pk):
    """
    Generic view function that updates an object from a specified model.

    Args:
        request: Django HTTP request
        model_name: String name of the model to update an object from
        pk: Primary key of the object to update

    Returns:
        Rendered form template or redirects to the list view on success
    """
    # Model adı ve model sınıfı eşleştirmesi
    model_map = {
        'sirket': Sirket,
        'tour': Tour,
        'transfer': Transfer,
        'vehicle': Vehicle,
        'guide': Guide,
        'hotel': Hotel,
        'activity': Activity,
        'museum': Museum,
        'supplier': Supplier,
        'activitysupplier': Activitysupplier,
        'cost': Cost,
        'activitycost': Activitycost,
        'buyercompany': Buyercompany,
        'personel': Personel,
    }

    # Form adı ve form sınıfı eşleştirmesi
    form_map = {
        'sirket': SirketForm,
        'tour': TourForm,
        'transfer': TransferForm,
        'vehicle': VehicleForm,
        'guide': GuideForm,
        'hotel': HotelForm,
        'activity': ActivityForm,
        'museum': MuseumForm,
        'supplier': SupplierForm,
        'activitysupplier': ActivitysupplierForm,
        'cost': CostForm,
        'activitycost': ActivitycostForm,
        'buyercompany': BuyercompanyForm,
        'personel': PersonelForm,
    }

    # Model adını kontrol et
    if model_name.lower() not in model_map:
        raise Http404(f"Model '{model_name}' bulunamadı")

    # Model ve form sınıflarını al
    model = model_map[model_name.lower()]
    form_class = form_map[model_name.lower()]

    # Nesneyi veritabanından al
    try:
        obj = get_object_or_404(model, pk=pk)
    except:
        messages.error(request, f"{model._meta.verbose_name} bulunamadı.")
        return redirect('tour:' + model_name.lower() + '_list')

    # Form görüntüleme ve işleme
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            # Değişiklikten önce mevcut veriyi kaydet (karşılaştırma için)
            old_data = {}
            for field in model._meta.fields:
                if field.name not in ['id', 'updated_at', 'is_delete']:
                    old_data[field.name] = getattr(obj, field.name)

            # Formu kaydet
            updated_instance = form.save()

            # Güncellenmiş nesne için log oluştur
            staff = None
            company = None

            if hasattr(request.user, 'personel') and request.user.personel.exists():
                staff = request.user.personel.first()
                company = staff.company

                # Personel için log kaydı
                log_action = f"{model._meta.verbose_name} güncelledi. Detaylar: "

                # Değişiklik olan alanları belirle
                for field in model._meta.fields:
                    if field.name not in ['id', 'created_at', 'updated_at', 'is_delete']:
                        old_value = old_data.get(field.name)
                        new_value = getattr(updated_instance, field.name)

                        # Değişiklik varsa loga ekle
                        if old_value != new_value:
                            log_action += f"{field.verbose_name}: {old_value} -> {new_value}, "

                # Son virgülü kaldır
                log_action = log_action.rstrip(', ')

                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=log_action,
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
            elif request.user.is_superuser:
                # Süper kullanıcı için log kaydı
                log_action = f"Süper kullanıcı {model._meta.verbose_name} güncelledi. Detaylar: "

                # Değişiklik olan alanları belirle
                for field in model._meta.fields:
                    if field.name not in ['id', 'created_at', 'updated_at', 'is_delete']:
                        old_value = old_data.get(field.name)
                        new_value = getattr(updated_instance, field.name)

                        # Değişiklik varsa loga ekle
                        if old_value != new_value:
                            log_action += f"{field.verbose_name}: {old_value} -> {new_value}, "

                # Son virgülü kaldır
                log_action = log_action.rstrip(', ')

                UserActivityLog.objects.create(
                    action=log_action,
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )

            messages.success(request, f"{model._meta.verbose_name} başarıyla güncellendi.")
            return redirect('tour:' + model_name.lower() + '_list')
    else:
        form = form_class(instance=obj)

    # Template değişkenleri
    context = {
        'form': form,
        'model_name': model_name,
        'model_verbose_name': model._meta.verbose_name,
        'action': 'Güncelle',
        'object': obj,
    }

    return render(request, 'generic/form.html', context)

@login_required(login_url='tour:login')
def generic_delete(request, model_name, pk):
    """
    Generic view function that deletes an object from a specified model.

    Args:
        request: Django HTTP request
        model_name: String name of the model to delete an object from
        pk: Primary key of the object to delete

    Returns:
        Redirects to the list view
    """
    # Model adı ve model sınıfı eşleştirmesi
    model_map = {
        'sirket': Sirket,
        'tour': Tour,
        'transfer': Transfer,
        'vehicle': Vehicle,
        'guide': Guide,
        'hotel': Hotel,
        'activity': Activity,
        'museum': Museum,
        'supplier': Supplier,
        'activitysupplier': Activitysupplier,
        'cost': Cost,
        'activitycost': Activitycost,
        'buyercompany': Buyercompany,
        'personel': Personel,
    }

    # Model adını kontrol et
    if model_name.lower() not in model_map:
        raise Http404(f"Model '{model_name}' bulunamadı")

    # Model sınıfını al
    model = model_map[model_name.lower()]

    # Nesneyi veritabanından al
    try:
        obj = get_object_or_404(model, pk=pk)
    except:
        messages.error(request, f"{model._meta.verbose_name} bulunamadı.")
        return redirect('tour:' + model_name.lower() + '_list')

    # Nesneyi sil (gerçek silme değil, is_delete=True yap)
    try:
        # Silme işleminden önce nesne detaylarını kaydet
        log_details = ""
        for field in model._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at', 'is_delete']:
                field_value = getattr(obj, field.name)
                if field_value is not None:
                    log_details += f"{field.verbose_name}: {field_value}, "

        # Son virgülü kaldır
        log_details = log_details.rstrip(', ')

        if hasattr(obj, 'is_delete'):
            obj.is_delete = True
            obj.save()
            messages.success(request, f"{model._meta.verbose_name} başarıyla silindi.")

            # Log kaydı oluştur
            staff = None
            company = None

            if hasattr(request.user, 'personel') and request.user.personel.exists():
                staff = request.user.personel.first()
                company = staff.company

                # Personel için log kaydı
                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=f"{model._meta.verbose_name} sildi. Detaylar: {log_details}",
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
            elif request.user.is_superuser:
                # Süper kullanıcı için log kaydı
                UserActivityLog.objects.create(
                    action=f"Süper kullanıcı {model._meta.verbose_name} sildi. Detaylar: {log_details}",
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
        else:
            # Eğer is_delete alanı yoksa gerçekten sil
            obj.delete()
            messages.success(request, f"{model._meta.verbose_name} başarıyla silindi.")

            # Log kaydı oluştur
            staff = None
            company = None

            if hasattr(request.user, 'personel') and request.user.personel.exists():
                staff = request.user.personel.first()
                company = staff.company

                # Personel için log kaydı
                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=f"{model._meta.verbose_name} kalıcı olarak sildi. Detaylar: {log_details}",
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
            elif request.user.is_superuser:
                # Süper kullanıcı için log kaydı
                UserActivityLog.objects.create(
                    action=f"Süper kullanıcı {model._meta.verbose_name} kalıcı olarak sildi. Detaylar: {log_details}",
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
    except Exception as e:
        messages.error(request, f"Hata oluştu: {str(e)}")

    return redirect('tour:' + model_name.lower() + '_list')

@login_required(login_url='tour:login')
def generic_deleted_list(request, model_name):
    """
    Generic view function that lists deleted objects (is_delete=True) from a specified model.

    Args:
        request: Django HTTP request
        model_name: String name of the model to list deleted objects from

    Returns:
        Rendered template with deleted model objects
    """
    # Model adı ve model sınıfı eşleştirmesi
    model_map = {
        'sirket': Sirket,
        'tour': Tour,
        'transfer': Transfer,
        'vehicle': Vehicle,
        'guide': Guide,
        'hotel': Hotel,
        'activity': Activity,
        'museum': Museum,
        'supplier': Supplier,
        'activitysupplier': Activitysupplier,
        'cost': Cost,
        'activitycost': Activitycost,
        'buyercompany': Buyercompany,
        'personel': Personel,
    }

    # Model adını kontrol et
    if model_name.lower() not in model_map:
        raise Http404(f"Model '{model_name}' bulunamadı")

    # Model sınıfını al
    model = model_map[model_name.lower()]

    # Arama sorgusu
    query = request.GET.get('q')

    # Eğer kullanıcı bir şirket personeli ise, sadece kendi şirketinin verilerini göster
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        personel = request.user.personel.first()
        company = personel.company
        # is_delete=True olan ve şirkete ait silinmiş kayıtları getir
        queryset = model.objects.filter(company=company, is_delete=True)
    else:
        # Admin için tüm silinmiş kayıtları getir
        queryset = model.objects.filter(is_delete=True)

    # Arama işlemi
    if query:
        # Model alanlarını al
        search_fields = []
        for field in model._meta.fields:
            # Sadece metin tabanlı alanları ekle
            if field.get_internal_type() in ['CharField', 'TextField']:
                search_fields.append(field.name)

        # Dinamik Q nesnesi oluştur
        if search_fields:
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})

            queryset = queryset.filter(q_objects)

    # Şablona göndereceğimiz context
    context = {
        'objects': queryset,
        'model_name': model_name,
        'model_verbose_name': model._meta.verbose_name,
        'model_verbose_name_plural': model._meta.verbose_name_plural,
        'query': query,  # Arama sorgusunu context'e ekle
        'is_deleted_list': True,  # Silinmiş öğeler listesi olduğunu belirt
    }

    # Silinmiş liste görüntüleme log kaydı oluştur
    company = None
    staff = None

    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company

        # Personel için log kaydı
        UserActivityLog.objects.create(
            company=company,
            staff=staff,
            action=f"Silinmiş {model._meta.verbose_name_plural} listesini ziyaret etti",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )
    elif request.user.is_superuser:
        # Süper kullanıcı için log kaydı
        UserActivityLog.objects.create(
            action=f"Süper kullanıcı silinmiş {model._meta.verbose_name_plural} listesini ziyaret etti",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )

    # Generic template kullan
    return render(request, 'generic/deleted_list.html', context)

@login_required(login_url='tour:login')
def restore_object(request, model_name, pk):
    """
    Generic view function that restores a deleted object (sets is_delete=False).

    Args:
        request: Django HTTP request
        model_name: String name of the model to restore an object from
        pk: Primary key of the object to restore

    Returns:
        Redirects to the deleted items list view
    """
    # Model adı ve model sınıfı eşleştirmesi
    model_map = {
        'sirket': Sirket,
        'tour': Tour,
        'transfer': Transfer,
        'vehicle': Vehicle,
        'guide': Guide,
        'hotel': Hotel,
        'activity': Activity,
        'museum': Museum,
        'supplier': Supplier,
        'activitysupplier': Activitysupplier,
        'cost': Cost,
        'activitycost': Activitycost,
        'buyercompany': Buyercompany,
        'personel': Personel,
    }

    # Model adını kontrol et
    if model_name.lower() not in model_map:
        raise Http404(f"Model '{model_name}' bulunamadı")

    # Model sınıfını al
    model = model_map[model_name.lower()]

    # Nesneyi veritabanından al
    try:
        obj = get_object_or_404(model, pk=pk, is_delete=True)
    except:
        messages.error(request, f"Silinmiş {model._meta.verbose_name} bulunamadı.")
        return redirect('tour:' + model_name.lower() + '_deleted_list')

    # Nesneyi geri getir (is_delete=False yap)
    try:
        # Geri getirme işleminden önce nesne detaylarını kaydet
        log_details = ""
        for field in model._meta.fields:
            if field.name not in ['id', 'created_at', 'updated_at', 'is_delete']:
                field_value = getattr(obj, field.name)
                if field_value is not None:
                    log_details += f"{field.verbose_name}: {field_value}, "

        # Son virgülü kaldır
        log_details = log_details.rstrip(', ')

        obj.is_delete = False
        obj.save()

        # Log kaydı oluştur
        staff = None
        company = None

        if hasattr(request.user, 'personel') and request.user.personel.exists():
            staff = request.user.personel.first()
            company = staff.company

            # Personel için log kaydı
            UserActivityLog.objects.create(
                company=company,
                staff=staff,
                action=f"{model._meta.verbose_name} geri getirdi. Detaylar: {log_details}",
                ip_address=get_client_ip(request),
                browser_info=request.META.get('HTTP_USER_AGENT', '')
            )
        elif request.user.is_superuser:
            # Süper kullanıcı için log kaydı
            UserActivityLog.objects.create(
                action=f"Süper kullanıcı {model._meta.verbose_name} geri getirdi. Detaylar: {log_details}",
                ip_address=get_client_ip(request),
                browser_info=request.META.get('HTTP_USER_AGENT', '')
            )

        messages.success(request, f"{model._meta.verbose_name} başarıyla geri getirildi.")
    except Exception as e:
        messages.error(request, f"Hata oluştu: {str(e)}")

    return redirect('tour:' + model_name.lower() + '_deleted_list')

# Yardımcı fonksiyon: Kullanıcının IP adresini almak için
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required(login_url='tour:login')
def my_user_activity_log(request):
    """
    Kullanıcının kendi aktivite kayıtlarını görüntüleyen view fonksiyonu.
    Son 3 günlük kayıtları gösterir.

    Args:
        request: Django HTTP request

    Returns:
        Kullanıcı aktivite loglarını listeleyen sayfayı render eder
    """
    try:
        # Son 3 günlük kayıtları alacak tarih hesaplaması
        son_uc_gun = timezone.now() - timezone.timedelta(days=3)

        # Başlık ve sayfa açıklaması
        title = "SON 3 GÜNLÜK KULLANICI AKTİVİTE KAYITLARIM"

        if hasattr(request.user, 'personel') and request.user.personel.exists():
            # Personelin kendi loglarını getir (son 3 gün)
            staff = request.user.personel.first()
            company = staff.company
            user_activity_logs = UserActivityLog.objects.filter(
                staff=staff,
                timestamp__gte=son_uc_gun
            ).order_by('-timestamp')

            # Log oluştur - kullanıcı kendi aktivite kayıtlarını görüntüledi
            UserActivityLog.objects.create(
                company=company,
                staff=staff,
                action="Son 3 günlük aktivite kayıtlarını görüntüledi",
                ip_address=get_client_ip(request),
                browser_info=request.META.get('HTTP_USER_AGENT', '')
            )
        elif request.user.is_superuser:
            # Süper kullanıcı tüm kayıtları görüntüleyebilir (son 3 gün)
            title = "SON 3 GÜNLÜK TÜM KULLANICI AKTİVİTE KAYITLARI"
            user_activity_logs = UserActivityLog.objects.filter(
                timestamp__gte=son_uc_gun
            ).order_by('-timestamp')

            # Log oluştur - süper kullanıcı tüm aktivite kayıtlarını görüntüledi
            UserActivityLog.objects.create(
                action="Süper kullanıcı son 3 günlük tüm aktivite kayıtlarını görüntüledi",
                ip_address=get_client_ip(request),
                browser_info=request.META.get('HTTP_USER_AGENT', '')
            )
        else:
            # Personel olmayan kullanıcılar için boş liste döndür
            user_activity_logs = UserActivityLog.objects.none()
            messages.warning(request, "HESABINIZ HERHANGİ BİR ŞİRKETLE İLİŞKİLENDİRİLMEMİŞ!")

        context = {
            'page_title': title,
            'logs': user_activity_logs,
            'is_activity_log': True,  # Şablonda farklı görünüm için
            'filtre_tarih': son_uc_gun.strftime('%d.%m.%Y')  # Filtreleme tarihi bilgisi
        }

        return render(request, 'generic/activity_logs.html', context)

    except Exception as e:
        messages.error(request, f"AKTİVİTE KAYITLARI GÖRÜNTÜLENİRKEN HATA OLUŞTU: {str(e)}")
        return redirect('tour:dashboard')





def operation_create(request):
    """
    Yeni bir operasyon oluşturmak için view fonksiyonu
    """
    # Kullanıcı şirket bilgisi al
    company = None
    staff = None

    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company
    if request.user.is_superuser:
        company = Sirket.objects.get(id=1)

    if request.method == 'POST':
        form = OperationForm(request.POST, company=company)
        if form.is_valid():
            # Formu kaydet
            instance = form.save(commit=False)
            instance.company = company
            instance.selling_staff = staff
            instance.save()

            # Operasyon günlerini oluştur
            finish = instance.finish
            start = instance.start
            while start <= finish:
                Operationday.objects.create(
                    company=company,
                    operation=instance,
                    date=start
                )
                start += timezone.timedelta(days=1)

            # Log kaydı oluştur
            if staff:
                # Personel için log kaydı
                log_action = f"Yeni operasyon oluşturdu: {instance.ticket} (#{instance.buyer_company.name})"

                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=log_action,
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
            elif request.user.is_superuser:
                # Süper kullanıcı için log kaydı
                log_action = f"Süper kullanıcı yeni operasyon oluşturdu: {instance.ticket} (#{instance.buyer_company.name})"

                UserActivityLog.objects.create(
                    action=log_action,
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )

            messages.success(request, f"Operasyon başarıyla oluşturuldu: {instance.ticket} (#{instance.buyer_company.name})")
            return redirect('tour:operation_detail', pk=instance.id)  # İşlem sonrası yönlendirme
    else:
        form = OperationForm(company=company)

    return render(request, 'operation/create.html', {'form': form})


@login_required(login_url='tour:login')
def operation_detail(request, pk):
    """
    Operasyon detaylarını görüntülemek için view fonksiyonu.
    Performans için gerekli tüm öğeler önceden alınır ve ilişkisel sorgular optimize edilir.
    """
    # Cache anahtarı oluştur - kullanıcı ve operasyon ID'sine göre
    cache_key = f"operation_detail_{pk}_{request.user.id}"
    # Cacheden veriyi almaya çalış
    cached_data = cache.get(cache_key)

    # Eğer cache'de veri varsa, direkt olarak context'i döndür
    if cached_data:
        return render(request, 'operation/detail.html', cached_data)

    # Cache'de veri yoksa, veritabanından çek
    # select_related ile ilişkili modelleri tek sorguda getir
    operation = get_object_or_404(
        Operation.objects.select_related(
            'company',
            'selling_staff',
            'follow_staff',
            'buyer_company'
        ),
        pk=pk
    )

    # prefetch_related ile alt nesneleri ön belleğe al
    days = Operationday.objects.filter(operation=operation).order_by('day_number')

    # İlişkili tüm modelleri tek sorguda getir
    items = Operationitem.objects.filter(
        day__in=days
    ).select_related(
        'day',
        'tour',
        'transfer',
        'vehicle',
        'supplier',
        'hotel',
        'activity',
        'activity_supplier',
        'guide'
    ).order_by('day__day_number', 'pick_time')

    # Aktivite log kaydı
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company

        UserActivityLog.objects.create(
            company=company,
            staff=staff,
            action=f"Operasyon detayı görüntüledi: {operation.ticket}",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )
    elif request.user.is_superuser:
        UserActivityLog.objects.create(
            action=f"Süper kullanıcı operasyon detayı görüntüledi: {operation.ticket}",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )

    # Öğeleri günlere göre grupla (şablonda daha hızlı erişim için)
    items_by_day = {}
    for day in days:
        items_by_day[day.id] = []

    for item in items:
        items_by_day[item.day.id].append(item)

    # Context'i oluştur
    context = {
        'operation': operation,
        'days': days,
        'items': items,
        'items_by_day': items_by_day,
    }

    # Context'i cache'e ekle (5 dakika süreyle)
    cache.set(cache_key, context, 300)  # 300 saniye = 5 dakika

    return render(request, 'operation/detail.html', context)


def operation_edit(request, pk):
    operation = get_object_or_404(Operation, pk=pk)
    staff = None
    company = None
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company
    if request.method == 'POST':
        form = OperationForm(request.POST, instance=operation)
        if form.is_valid():
            form.save()
            #Log kaydı oluştur
            if staff:
                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=f"Operasyon gününde yeni öğe oluşturdu: {operation.ticket}",
                )
            elif request.user.is_superuser:
                UserActivityLog.objects.create(
                    action=f"Süper kullanıcı operasyon gününde yeni öğe oluşturdu: {operation.ticket}",
                )
            return render(request, 'operation/partials/operation-card.html', {'operation': operation})
        else:
            print(form.errors)
            #Log kaydı oluştur
            if staff:
                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=f"Operasyon gününde yeni öğe oluşturma sırasında hata oluştu: {operation.ticket}, Hata: {form.errors}",
                )
            elif request.user.is_superuser:
                UserActivityLog.objects.create(
                    action=f"Süper kullanıcı operasyon gününde yeni öğe oluşturma sırasında hata oluştu: {operation.ticket}, Hata: {form.errors}",
                )
    else:
        form = OperationForm(instance=operation)
        #Log kaydı oluştur
        if staff:
            UserActivityLog.objects.create(
                company=company,
                staff=staff,
                action=f"Operasyon gününde yeni öğe oluşturma sayfasını ziyaret etti: {operation.ticket}",
            )
        elif request.user.is_superuser:
            UserActivityLog.objects.create(
                action=f"Süper kullanıcı operasyon gününde yeni öğe oluşturma sayfasını ziyaret etti: {operation.ticket}",
            )

    return render(request, 'operation/edit.html', {'form': form, 'operation': operation})



def normalize_phone_number(phone=None):
    if phone is None:
        return None

    # Tüm karakterleri temizle (sadece rakamları al)
    digits = re.sub(r'\D', '', phone)

    # Eğer numara 11 haneli ve 0 ile başlıyorsa, baştaki 0'ı at
    if len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]

    # Eğer numara 12 haneli ve 90 ile başlıyorsa (ülke kodlu), baştaki 90'ı at
    if len(digits) == 12 and digits.startswith('90'):
        digits = digits[2:]

    # Son kontrol: Türk cep telefonu numarası 10 haneli olmalı
    if len(digits) == 10 and digits.startswith('5'):
        return digits
    else:
        return None  # Geçersiz numara


def operationitem_edit(request, pk):
    item = get_object_or_404(Operationitem, pk=pk)

    if item.driver:
        old_driver = item.driver
        if item.driver_phone:
            old_driver_phone = item.driver_phone
        else:
            old_driver_phone = None
    else:
        old_driver = None
    old_plaka = item.plaka
    old_pick_location = item.pick_location
    old_pick_time = item.pick_time


    if  item.guide:
        old_guide = item.guide
        if item.guide.phone:
            old_guide_phone = item.guide.phone
        else:
            old_guide_phone = None
    else:
        old_guide = None

    form = OperationItemForm(request.POST or None, instance=item)
    if request.method == 'POST':
        if form.is_valid():
            new_item = form.save()

            # Maliyet hesaplaması
            if new_item.manuel_vehicle_price != 0:
                new_item.vehicle_price = new_item.manuel_vehicle_price
            elif new_item.manuel_vehicle_price == 0 and new_item.operation_type == "Transfer":
                if new_item.transfer and new_item.vehicle and new_item.supplier and not new_item.vehicle_price:
                    cost = Cost.objects.get(transfer=new_item.transfer, supplier=new_item.supplier, is_delete=False, company=new_item.company)
                    if cost:
                        if new_item.vehicle.vehicle == "BINEK":
                            new_item.vehicle_price = cost.car
                        elif new_item.vehicle.vehicle == "MINIVAN":
                            new_item.vehicle_price = cost.minivan
                        elif new_item.vehicle.vehicle == "MINIBUS":
                            new_item.vehicle_price = cost.minibus
                        elif new_item.vehicle.vehicle == "MIDIBUS":
                            new_item.vehicle_price = cost.midibus
                        elif new_item.vehicle.vehicle == "OTOBUS":
                            new_item.vehicle_price = cost.bus
                    else:
                        print("Maliyet Bulunamadı")
            # Maliyet hesaplaması
            elif new_item.manuel_vehicle_price == 0 and (new_item.operation_type == "Tur" or new_item.manuel_vehicle_price == 0 and new_item.operation_type == "TurTransfer" or new_item.manuel_vehicle_price == 0 and new_item.operation_type == "TransferTur"):
                if new_item.tour and new_item.vehicle and new_item.supplier and not new_item.vehicle_price:
                    cost = Cost.objects.get(tour=new_item.tour, supplier=new_item.supplier, is_delete=False, company=new_item.company)
                    if cost:
                        if new_item.vehicle.vehicle == "BINEK":
                            new_item.vehicle_price = cost.car
                        elif new_item.vehicle.vehicle == "MINIVAN":
                            new_item.vehicle_price = cost.minivan
                        elif new_item.vehicle.vehicle == "MINIBUS":
                            new_item.vehicle_price = cost.minibus
                        elif new_item.vehicle.vehicle == "MIDIBUS":
                            new_item.vehicle_price = cost.midibus
                        elif new_item.vehicle.vehicle == "OTOBUS":
                            new_item.vehicle_price = cost.bus
                    else:
                        print("Maliyet Bulunamadı")
            new_item.save()

            if new_item.operation_type == "Transfer":
                if new_item.transfer and new_item.vehicle and new_item.pick_time and new_item.supplier and new_item.driver and new_item.driver_phone and new_item.plaka and new_item.day.date >= (timezone.now().date()) and new_item.pick_location:
                    sms(normalize_phone_number(new_item.driver_phone), f"Sayın {new_item.driver}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı araçla {new_item.pick_location} adresine Misafirlerimizle buluşmak üzere {new_item.transfer.route} Transfer tanımlanmıştır.")
                    if new_item.guide:
                        sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı {new_item.transfer.route} Transfer tanımlanmıştır. Araç Şoförü: {new_item.driver} Telefon: {new_item.driver_phone}")
            if new_item.operation_type == "Tur" or new_item.operation_type == "TurTransfer" or new_item.operation_type == "TransferTur":
                if new_item.tour and new_item.vehicle and new_item.pick_time and new_item.supplier and new_item.driver and new_item.driver_phone and new_item.plaka and new_item.day.date >= (timezone.now().date()) and new_item.pick_location:
                    sms(normalize_phone_number(new_item.driver_phone), f"Sayın {new_item.driver}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı araçla {new_item.pick_location} adresine Misafirlerimizle buluşmak üzere {new_item.tour.route} Tur tanımlanmıştır.")
                    if new_item.guide:
                        sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı {new_item.tour.route} Tur tanımlanmıştır. Araç Şoförü: {new_item.driver} Telefon: {new_item.driver_phone}")
            if new_item.operation_type == "Rehber":
                if new_item.guide and new_item.tour.route == "WALKING TUR IST" and new_item.day.date >= (timezone.now().date()) and new_item.pick_time and new_item.pick_location:
                    sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.pick_location} adresinde Misafirlerimizle buluşmak üzere {new_item.tour.route} Turu tanımlanmıştır.")
                elif new_item.guide and new_item.day.date >= (timezone.now().date()) and new_item.pick_time and new_item.pick_location:
                    sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.pick_location} adresinde Misafirlerimizle buluşmak üzere Rehber olarak görev tanımlanmıştır.")
            if new_item.operation_type == "Aracli Rehber":
                if new_item.guide and new_item.day.date >= (timezone.now().date()) and new_item.pick_time and new_item.pick_location:
                    sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.pick_location} adresine Misafirlerimizle buluşmak üzere Araçlı Rehber olarak görev tanımlanmıştır.")
            if old_driver != new_item.driver and old_driver_phone:
                sms(old_driver_phone, f"Sayın {old_driver}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {old_pick_time} saatindeki işiniz iptal edildi.")
                if new_item.operation_type == "Transfer":
                    if new_item.transfer and new_item.vehicle and new_item.pick_time and new_item.supplier and new_item.driver and new_item.driver_phone and new_item.plaka and new_item.day.date >= (timezone.now().date()) and new_item.pick_location:
                        sms(normalize_phone_number(new_item.driver_phone), f"Sayın {new_item.driver}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı araçla {new_item.pick_location} adresine Misafirlerimizle buluşmak üzere {new_item.transfer.route} Transfer tanımlanmıştır.")
                        if new_item.guide:
                            sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı {new_item.transfer.route} Transfer tanımlanmıştır. Yeni Araç Şoförü: {new_item.driver} Telefon: {new_item.driver_phone}")
                if new_item.operation_type == "Tur" or new_item.operation_type == "TurTransfer" or new_item.operation_type == "TransferTur":
                    if new_item.tour and new_item.vehicle and new_item.pick_time and new_item.supplier and new_item.driver and new_item.driver_phone and new_item.plaka and new_item.day.date >= (timezone.now().date()) and new_item.pick_location:
                        sms(normalize_phone_number(new_item.driver_phone), f"Sayın {new_item.driver}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı araçla {new_item.pick_location} adresine Misafirlerimizle buluşmak üzere {new_item.tour.route} Tur tanımlanmıştır.")
                        if new_item.guide:
                            sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı {new_item.tour.route} Tur tanımlanmıştır. YeniAraç Şoförü: {new_item.driver} Telefon: {new_item.driver_phone}")
            if old_guide != new_item.guide and old_guide_phone:
                sms(normalize_phone_number(old_guide_phone), f"Sayın {old_guide}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {old_pick_time} saatindeki işiniz iptal edildi.")
                if new_item.operation_type == "Transfer":
                    if new_item.transfer and new_item.vehicle and new_item.pick_time and new_item.supplier and new_item.driver and new_item.driver_phone and new_item.plaka and new_item.day.date >= (timezone.now().date()) and new_item.pick_location and new_item.guide:
                        sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı {new_item.transfer.route} Transfer tanımlanmıştır. Araç Şoförü: {new_item.driver} Telefon: {new_item.driver_phone}")
                if new_item.operation_type == "Tur" or new_item.operation_type == "TurTransfer" or new_item.operation_type == "TransferTur":
                    if new_item.tour and new_item.vehicle and new_item.pick_time and new_item.supplier and new_item.driver and new_item.driver_phone and new_item.plaka and new_item.day.date >= (timezone.now().date()) and new_item.pick_location and new_item.guide:
                        sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.plaka} plakalı {new_item.tour.route} Tur tanımlanmıştır. Araç Şoförü: {new_item.driver} Telefon: {new_item.driver_phone}")
                    if new_item.operation_type == "Rehber":
                        if new_item.guide and new_item.tour.route == "WALKING TUR IST" and new_item.day.date >= (timezone.now().date()) and new_item.pick_time and new_item.pick_location:
                            sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.pick_location} adresinde Misafirlerimizle buluşmak üzere {new_item.tour.route} Turu tanımlanmıştır.")
                        elif new_item.guide and new_item.day.date >= (timezone.now().date()) and new_item.pick_time and new_item.pick_location:
                            sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.pick_location} adresinde Misafirlerimizle buluşmak üzere Rehber olarak görev tanımlanmıştır.")
                    if new_item.operation_type == "Aracli Rehber":
                        if new_item.guide and new_item.day.date >= (timezone.now().date()) and new_item.pick_time and new_item.pick_location:
                            sms(normalize_phone_number(new_item.guide.phone), f"Sayın {new_item.guide.name}. {new_item.day.date.strftime('%d.%m.%Y')} tarihinde {new_item.pick_time} saatinde, {new_item.pick_location} adresine Misafirlerimizle buluşmak üzere Araçlı Rehber olarak görev tanımlanmıştır.")
            return render(request, 'operation/partials/item-table.html', {'item': new_item})
        else:
            print(form.errors)
    else:
        return render(request, 'operation/item-edit.html', {'form': form, 'item': item})


def operation_delete(request, pk):
    pass

def operationitem_delete(request, pk):
    pass



def operationday_item_create(request, day_id):
    day = get_object_or_404(Operationday, id=day_id)
    staff = None
    company = None

    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company

    if request.user.is_superuser:
        company = Sirket.objects.get(id=1)

    if request.method == 'POST':
        form = OperationItemForm(request.POST, company=company)
        if form.is_valid():
            item = form.save(commit=False)
            item.day = day
            item.company = company
            item.save()
            form.save_m2m()  # ManyToMany ilişkilerini kaydet

            # Log kaydı oluştur
            if staff:
                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=f"Operasyon gününde yeni öğe oluşturdu: {item.operation_type}",
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )
            elif request.user.is_superuser:
                UserActivityLog.objects.create(
                    action=f"Süper kullanıcı operasyon gününde yeni öğe oluşturdu: {item.operation_type}",
                    ip_address=get_client_ip(request),
                    browser_info=request.META.get('HTTP_USER_AGENT', '')
                )

            return render(request, 'operation/partials/item-table.html', {'item': item})
        else:
            print(form.errors)
            #Log kaydı oluştur
            if staff:
                UserActivityLog.objects.create(
                    company=company,
                    staff=staff,
                    action=f"Operasyon gününde yeni öğe oluşturma sırasında hata oluştu: {item.operation_type}, {day.date}, {item.id}, Hata: {form.errors}",
                )
            elif request.user.is_superuser:
                UserActivityLog.objects.create(
                    action=f"Süper kullanıcı operasyon gününde yeni öğe oluşturma sırasında hata oluştu: {item.operation_type}, {day.date}, {item.id}, Hata: {form.errors}",
                )
    else:
        form = OperationItemForm(company=company)
        #Log kaydı oluştur
        if staff:
            UserActivityLog.objects.create(
                company=company,
                staff=staff,
                action=f"Operasyon gününde yeni öğe oluşturma sayfasını ziyaret etti: {day.date}",
            )
        elif request.user.is_superuser:
            UserActivityLog.objects.create(
                action=f"Süper kullanıcı operasyon gününde yeni öğe oluşturma sayfasını ziyaret etti: {day.date}",
            )

    return render(request, 'operation/partials/item-create.html', {'form': form, 'day': day})

def operation_list(request):
    """
    Operasyonları aylara, yıllara ve diğer kriterlere göre listeleyen view fonksiyonu.

    Aylara ve diğer kriterlere göre filtreleme yapılabilir.
    Ay seçilmediğinde, mevcut tarih ayı varsayılan olarak seçilir.
    """
    # Filtre parametrelerini al
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    ticket = request.GET.get('ticket', '')
    buyer_company_id = request.GET.get('buyer_company', '')
    selling_staff_id = request.GET.get('selling_staff', '')
    follow_staff_id = request.GET.get('follow_staff', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Şirket bilgisini al
    company = None
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        company = request.user.personel.first().company

    # Temel sorgu - şirkete ait operasyonlar veya admin için tüm operasyonlar
    if company:
        queryset = Operation.objects.filter(company=company, is_delete=False).select_related('buyer_company', 'selling_staff', 'follow_staff')
    elif request.user.is_superuser:
        queryset = Operation.objects.filter(is_delete=False).select_related('buyer_company', 'selling_staff', 'follow_staff')
    else:
        queryset = Operation.objects.none()

    # Ay filtreleme
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Ay seçilmemişse ve diğer filtreler de yoksa, varsayılan olarak mevcut ayı seç
    if not month and not any([ticket, buyer_company_id, selling_staff_id, follow_staff_id, start_date, end_date]):
        month = str(current_month)

    # Yıl seçilmemişse ve ay seçilmişse, varsayılan olarak mevcut yılı seç
    if month and not year:
        year = str(current_year)

    # Filtreleri uygula
    if month and year:
        month_int = int(month)
        year_int = int(year)

        # Ay başlangıç ve bitiş tarihleri
        month_start = timezone.datetime(year_int, month_int, 1).date()
        if month_int == 12:
            month_end = timezone.datetime(year_int + 1, 1, 1).date() - timezone.timedelta(days=1)
        else:
            month_end = timezone.datetime(year_int, month_int + 1, 1).date() - timezone.timedelta(days=1)

        # Operasyonun tarihi, seçilen ay ile kesişiyorsa filtrele
        queryset = queryset.filter(
            Q(start__lte=month_end) & Q(finish__gte=month_start)
        )

    # Diğer filtreleri uygula
    if ticket:
        queryset = queryset.filter(ticket__icontains=ticket)

    if buyer_company_id:
        queryset = queryset.filter(buyer_company_id=buyer_company_id)

    if selling_staff_id:
        queryset = queryset.filter(selling_staff_id=selling_staff_id)

    if follow_staff_id:
        queryset = queryset.filter(follow_staff_id=follow_staff_id)

    if start_date:
        queryset = queryset.filter(start__gte=start_date)

    if end_date:
        queryset = queryset.filter(finish__lte=end_date)

    # İstatistik bilgileri
    today = timezone.now().date()

    # Tamamlanan operasyonlar (bitiş tarihi geçmiş)
    completed_count = queryset.filter(finish__lt=today).count()

    # Aktif operasyonlar (başlangıç tarihi geçmiş ve bitiş tarihi gelmemiş)
    active_count = queryset.filter(start__lte=today, finish__gte=today).count()

    # Gelecek operasyonlar (başlangıç tarihi gelecekte)
    upcoming_count = queryset.filter(start__gt=today).count()

    # Yıl listesi - tüm operasyonlardaki yılları al
    year_list = set()
    all_operations = Operation.objects.all()
    for op in all_operations:
        if op.start:
            year_list.add(op.start.year)
        if op.finish:
            year_list.add(op.finish.year)
    year_list = sorted(list(year_list))

    # Müşteri şirketlerini getir
    if company:
        companies = Buyercompany.objects.filter(company=company, is_delete=False)
    elif request.user.is_superuser:
        companies = Buyercompany.objects.filter(is_delete=False)
    else:
        companies = Buyercompany.objects.none()

    # Personel listesi
    if company:
        staffs = Personel.objects.filter(company=company, is_active=True)
    elif request.user.is_superuser:
        staffs = Personel.objects.filter(is_active=True)
    else:
        staffs = Personel.objects.none()

    # Operasyonları başlangıç tarihine göre sırala
    operations = queryset.order_by('-start')

    # Log kaydı oluştur
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()

        UserActivityLog.objects.create(
            company=company,
            staff=staff,
            action=f"Operasyon listesini görüntüledi",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )
    elif request.user.is_superuser:
        UserActivityLog.objects.create(
            action=f"Süper kullanıcı operasyon listesini görüntüledi",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )

    context = {
        'operations': operations,
        'selected_month': month,
        'selected_year': year,
        'year_list': year_list,
        'companies': companies,
        'staffs': staffs,
        'completed_count': completed_count,
        'active_count': active_count,
        'upcoming_count': upcoming_count,
    }

    return render(request, 'operation/list.html', context)


def job_list(request):
    # Kullanıcı bilgilerini tek seferde al
    today = timezone.now().date()
    tomorrow = today + timezone.timedelta(days=1)
    nextday = today + timezone.timedelta(days=2)
    job = True

    company = None
    staff = None
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company

    # Performans için ilişkili modelleri tek sorguda getir
    # Her sorgunun kendine özgü cache anahtarı olacak
    cache_prefix = f"job_list_{company.id if company else 'admin'}"

    # Temel sorgu yapısını oluştur - sadece gerekli alanları seç
    base_query = Operationitem.objects.select_related(
        'day',
        'day__operation',
        'day__operation__follow_staff',
        'tour',
        'transfer',
        'vehicle',
        'supplier'
    ).filter(is_delete=False)

    # Arama işlemi
    search_date = None
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if start_date:
            # Önbellek anahtarı oluştur
            search_cache_key = f"{cache_prefix}_search_{start_date}_{end_date}"
            # Önbellekten veriyi almaya çalış
            search_date = cache.get(search_cache_key)

            # Önbellekte yoksa veritabanından çek
            if search_date is None:
                search_query = base_query
                if company:
                    search_query = search_query.filter(company=company)

                if not end_date:
                    # Tek gün araması
                    search_date = search_query.filter(day__date=start_date).order_by('pick_time')
                else:
                    # Tarih aralığı araması
                    search_date = search_query.filter(
                        day__date__range=(start_date, end_date)
                    ).order_by('day__date', 'pick_time')

                # Sonuçları önbelleğe al (5 dakika)
                cache.set(search_cache_key, search_date, 300)

    # Günlük verileri sorgula - önbellekleme ile optimizasyon
    today_cache_key = f"{cache_prefix}_today_{today}"
    tomorrow_cache_key = f"{cache_prefix}_tomorrow_{tomorrow}"
    nextday_cache_key = f"{cache_prefix}_nextday_{nextday}"

    # Bugün için önbellekten kontrol
    today_items = cache.get(today_cache_key)
    if today_items is None:
        today_items = base_query.filter(day__date=today).order_by('pick_time')
        cache.set(today_cache_key, today_items, 300)  # 5 dakika önbellek

    # Yarın için önbellekten kontrol
    tomorrow_items = cache.get(tomorrow_cache_key)
    if tomorrow_items is None:
        tomorrow_items = base_query.filter(day__date=tomorrow).order_by('pick_time')
        cache.set(tomorrow_cache_key, tomorrow_items, 300)

    # Sonraki gün için önbellekten kontrol
    nextday_items = cache.get(nextday_cache_key)
    if nextday_items is None:
        nextday_items = base_query.filter(day__date=nextday).order_by('pick_time')
        cache.set(nextday_cache_key, nextday_items, 300)

    # Log kaydı oluştur - DRY prensibine uygun kod
    if staff:
        UserActivityLog.objects.create(
            company=company,
            staff=staff,
            action="Günlük iş listesini görüntüledi",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )
    elif request.user.is_superuser:
        UserActivityLog.objects.create(
            action="Süper kullanıcı günlük iş listesini görüntüledi",
            ip_address=get_client_ip(request),
            browser_info=request.META.get('HTTP_USER_AGENT', '')
        )

    # Tek bir context dictionary oluştur
    context = {
        'today': today,
        'tomorrow': tomorrow,
        'nextday': nextday,
        'today_items': today_items,
        'tomorrow_items': tomorrow_items,
        'nextday_items': nextday_items,
        'job': job
    }

    # Arama sonuçları varsa ekle
    if search_date is not None:
        context['search_date'] = search_date

    return render(request, 'job/list.html', context)

def my_job_list(request):
    # Kullanıcı bilgilerini tek seferde al
    today = timezone.now().date()
    tomorrow = today + timezone.timedelta(days=1)
    nextday = today + timezone.timedelta(days=2)

    # Kullanıcı kontrolü
    staff = None
    company = None
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        staff = request.user.personel.first()
        company = staff.company
    else:
        # Personel yoksa boş sayfa göster
        return render(request, 'job/list.html', {
            'today': today,
            'tomorrow': tomorrow,
            'nextday': nextday,
            'today_items': [],
            'tomorrow_items': [],
            'nextday_items': []
        })

    # Performans için ilişkili modelleri tek sorguda getir
    base_query = Operationitem.objects.select_related(
        'day',
        'day__operation',
        'day__operation__follow_staff',
        'day__operation__follow_staff__user',
        'tour',
        'transfer',
        'vehicle'
    ).filter(day__operation__follow_staff=staff)

    # Arama işlemi
    search_date = None
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if start_date:
            if not end_date:
                # Tek gün araması
                search_date = base_query.filter(day__date=start_date).order_by('pick_time')
            else:
                # Tarih aralığı araması
                search_date = base_query.filter(
                    day__date__range=(start_date, end_date)
                ).order_by('day__date', 'pick_time')

    # Günlük verileri sorgula
    today_items = base_query.filter(day__date=today).order_by('pick_time')
    tomorrow_items = base_query.filter(day__date=tomorrow).order_by('pick_time')
    nextday_items = base_query.filter(day__date=nextday).order_by('pick_time')

    # Log kaydı oluştur
    UserActivityLog.objects.create(
        company=company,
        staff=staff,
        action="Kişisel iş listesini görüntüledi",
        ip_address=get_client_ip(request),
        browser_info=request.META.get('HTTP_USER_AGENT', '')
    )

    # Tek bir context dictionary oluştur
    context = {
        'today': today,
        'tomorrow': tomorrow,
        'nextday': nextday,
        'today_items': today_items,
        'tomorrow_items': tomorrow_items,
        'nextday_items': nextday_items,
        'is_personal': True,  # Kişisel liste gösterimi için bayrak
        'job': True
    }

    # Arama sonuçları varsa ekle
    if search_date is not None:
        context['search_date'] = search_date

    return render(request, 'job/list.html', context)


def operationitemfile_create(request, pk):
    operation_item = get_object_or_404(Operationitem, pk=pk)
    if request.method == 'POST':
        form = OperationFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.operation = operation_item.day.operation
            file.operation_item = operation_item
            file.save()
            return render(request, 'operation/partials/item-table.html', {'item': operation_item})
    else:
        form = OperationFileForm()
    return render(request, 'operation/operationitemfile_form.html', {'form': form, 'item': operation_item})



def operationfile_create(request, pk):
    operation = get_object_or_404(Operation, pk=pk)
    if request.method == 'POST':
        form = OperationFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.operation = operation
            file.save()
            return render(request, 'operation/partials/operation-card.html', {'operation': operation})
    else:
        form = OperationFileForm()
    return render(request, 'operation/operationfile_form.html', {'form': form, 'operation': operation})


def sms(phone, mesaj):
    url = "https://api.netgsm.com.tr/sms/send/xml"
    headers = {'Content-Type': 'application/xml'}
    usercode = "8503081334"
    password = "F#D6C7B"
    appkey = "xxxx"

    # Sunucu IP'sini al
    try:
        response = requests.get('https://api.ipify.org?format=json')
        print(f"Sunucu IP: {response.json()['ip']}")
    except:
        print("IP adresi alınamadı")

    body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <mainbody>
           <header>
            <company>Netgsm</company>
               <usercode>{usercode}</usercode>
               <password>{password}</password>
               <type>n:n</type>
               <appkey>{appkey}</appkey>
               <msgheader>MNC GROUP</msgheader>
           </header>
           <body>
               <mp><msg><![CDATA[{mesaj}]]></msg><no>{phone}</no></mp>
           </body>
        </mainbody>"""

    try:
        response = requests.post(url, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        print(f"Request Body: {body}")
        response.raise_for_status()
        return True, "SMS başarıyla gönderildi"
    except requests.exceptions.RequestException as e:
        print(f"SMS gönderimi sırasında hata oluştu: {e}")
        return False, f"SMS gönderilemedi: {str(e)}"



def cost_calculate():
    import datetime
    tomorrow = datetime.date.today() - datetime.timedelta(days=1)
    items = Operationitem.objects.filter(day__date__gte=tomorrow)


    for new_item in items:
        if new_item.manuel_vehicle_price:
            new_item.vehicle_price = new_item.manuel_vehicle_price
        elif not new_item.vehicle_price and new_item.vehicle and new_item.supplier:
            cost = None
            if new_item.operation_type == "Transfer" and new_item.transfer:
                try:
                    cost = Cost.objects.get(
                        transfer=new_item.transfer,
                        supplier=new_item.supplier,
                        is_delete=False,
                        company=new_item.company
                    )
                except Cost.DoesNotExist:
                    print("Maliyet Bulunamadı")
            elif new_item.operation_type in ["Tur", "TurTransfer", "TransferTur"] and new_item.tour:
                try:
                    cost = Cost.objects.get(
                        tour=new_item.tour,
                        supplier=new_item.supplier,
                        is_delete=False,
                        company=new_item.company
                    )
                except Cost.DoesNotExist:
                    print("Maliyet Bulunamadı")

            if cost:
                vehicle_type = new_item.vehicle.vehicle
                vehicle_cost_map = {
                    "BINEK": cost.car,
                    "MINIVAN": cost.minivan,
                    "MINIBUS": cost.minibus,
                    "MIDIBUS": cost.midibus,
                    "OTOBUS": cost.bus
                }
                new_item.vehicle_price = vehicle_cost_map.get(vehicle_type, 0)

        new_item.save()