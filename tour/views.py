from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
import re
import requests
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from .models import *
from .forms import *
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.template.defaulttags import register
import random
import logging
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Prefetch
from django.db.models.functions import ExtractYear
from .utils import (
    apply_item_filters, get_client_ip, get_deleted_items_query, get_operation_log_message, normalize_phone_number, save_operation_form, send_sms,
    generate_sms_code, toggle_operation_day, toggle_operation_item, update_item_costs, validate_password, create_activity_log,
    get_user_company_info, get_model_and_form, get_model_fields_for_search,
    get_object_details, get_select_related_fields, get_filtered_queryset,
    get_base_activity_log_query, get_user_activity_logs, paginate_activity_logs,
    get_operation_with_relations, get_operation_detail_data, get_operation_detail_log_message,
    save_operation_edit_form, get_operation_edit_log_message, calculate_vehicle_price, send_operation_sms,
    save_operation_day_item, get_operation_day_log_message,
    get_operation_list_filters, get_operation_list_stats, get_operation_list_year_list, get_operation_list_context,
    get_job_list_dates, get_job_list_base_query, get_job_list_search_query, get_job_list_context,
    create_job_list_log, save_operation_file_form, get_operation_file_partial_template, get_operation_file_context_data,
    get_operation_file_template, get_operation_file_context,
    toggle_operation, toggle_operation_item,
    get_operation_toggle_log_message, get_operation_item_toggle_log_message,
    get_operation_day_toggle_log_message
)


logger = logging.getLogger(__name__)

# Create your views here.


def login_view(request):
    if request.user.is_authenticated:
        return redirect('tour:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                personel, company = get_user_company_info(user)

                if personel and company:
                    messages.success(request, f"HOŞGELDİNİZ, {user.get_full_name().upper()}")
                    create_activity_log(
                        company=company,
                        staff=personel,
                        action=f"Kullanıcı giriş yaptı: {user.username}",
                        request=request
                    )
                elif user.is_superuser:
                    messages.success(request, f"HOŞGELDİNİZ, {user.get_full_name().upper()}")
                    create_activity_log(
                        action=f"Süper kullanıcı giriş yaptı: {user.username}",
                        request=request
                    )
                else:
                    messages.warning(request, "HESABINIZ HERHANGİ BİR ŞİRKETLE İLİŞKİLENDİRİLMEMİŞ!")

                next_url = request.GET.get('next')
                return redirect(next_url if next_url else 'tour:dashboard')
            else:
                messages.error(request, "KULLANICI ADI VEYA ŞİFRE YANLIŞ!")
        else:
            messages.error(request, "LÜTFEN KULLANICI ADI VE ŞİFRE GİRİNİZ!")

    return render(request, 'login.html')

def logout_view(request):
    if request.user.is_authenticated:
        personel, company = get_user_company_info(request.user)
        create_activity_log(
            company=company,
            staff=personel,
            action=f"Kullanıcı çıkış yaptı: {request.user.username}",
            request=request
        )

    logout(request)
    messages.success(request, "BAŞARIYLA ÇIKIŞ YAPTINIZ!")
    return redirect('tour:login')

def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            sms_code = generate_sms_code()
            cache_key = f'password_reset_{username}'
            cache.set(cache_key, sms_code, timeout=300)

            try:
                personel, _ = get_user_company_info(user)
                if not personel:
                    raise Exception("Kullanıcı personel bilgisi bulunamadı")
                    
                message = f"Sayın {user.get_full_name().upper()}, Şifre sıfırlama kodunuz: {sms_code}"
                success, _ = send_sms(normalize_phone_number(personel.phone), message)
                
                if success:
                    messages.success(request, 'SMS kodu telefonunuza gönderildi.')
                    return redirect('tour:reset_password', username=username)
                else:
                    raise Exception("SMS gönderilemedi")
                    
            except Exception as e:
                logger.error(f"SMS gönderme hatası: {str(e)}")
                messages.error(request, 'SMS gönderilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
        except User.DoesNotExist:
            messages.error(request, 'Kullanıcı bulunamadı!')
        except Exception as e:
            logger.error(f"Şifre sıfırlama hatası: {str(e)}")
            messages.error(request, 'Bir hata oluştu. Lütfen daha sonra tekrar deneyin.')

    return render(request, 'forgot_password.html', {'user_found': False})

def reset_password(request, username):
    try:
        user = User.objects.get(username=username)
        cache_key = f'password_reset_{username}'
        stored_code = cache.get(cache_key)

        if request.method == 'POST':
            user_code = request.POST.get('code')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not stored_code or user_code != stored_code:
                messages.error(request, 'Geçersiz veya süresi dolmuş SMS kodu!')
                return render(request, 'forgot_password.html', {'user_found': True, 'username': username})

            if not validate_password(request, new_password, confirm_password):
                return render(request, 'forgot_password.html', {'user_found': True, 'username': username})

            try:
                user.set_password(new_password)
                user.save()
                cache.delete(cache_key)
                messages.success(request, 'Şifreniz başarıyla güncellendi!')
                return redirect('tour:login')
            except Exception as e:
                logger.error(f"Şifre güncelleme hatası: {str(e)}")
                messages.error(request, 'Şifre güncellenirken bir hata oluştu.')
                return render(request, 'forgot_password.html', {'user_found': True, 'username': username})

        return render(request, 'forgot_password.html', {'user_found': True, 'username': username})
    except User.DoesNotExist:
        messages.error(request, 'Kullanıcı bulunamadı!')
        return redirect('tour:forgot_password')
    except Exception as e:
        logger.error(f"Şifre sıfırlama hatası: {str(e)}")
        messages.error(request, 'Bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
        return redirect('tour:forgot_password')
    

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Oturum bilgisini güncelle
            messages.success(request, 'Şifreniz başarıyla değiştirildi!')
            return redirect('tour:dashboard')
        else:
            messages.error(request, 'Lütfen hataları düzeltin.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'change_password.html', {
        'form': form,
        'title': 'Şifre Değiştir'
    })

@login_required(login_url='tour:login')
def dashboard(request):
    cache_key = f"dashboard_{request.user.id}"
    cache_timeout = 300

    cached_data = cache.get(cache_key)
    if cached_data:
        return render(request, 'dashboard.html', cached_data)

    personel, company = get_user_company_info(request.user)

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

    context = {
        'user': request.user,
        'company': company,
    }

    for model_name, model in models.items():
        active_query = get_filtered_queryset(model, request, is_deleted=False)
        deleted_query = get_filtered_queryset(model, request, is_deleted=True)

        context[f'{model_name}_count'] = active_query.count()
        context[f'deleted_{model_name}_count'] = deleted_query.count()

    if company and not request.user.is_superuser:
        recent_logs = UserActivityLog.objects.filter(
            company=company,
            staff=personel
        ).order_by('-timestamp')[:5]
    else:
        recent_logs = UserActivityLog.objects.all().order_by('-timestamp')[:5]

    context['recent_logs'] = recent_logs

    today = timezone.now().date()
    if company and not request.user.is_superuser:
        active_operations = Operation.objects.filter(
            company=company,
            is_delete=False,
            start__lte=today,
            finish__gte=today,
            follow_staff=personel
        ).select_related('buyer_company', 'follow_staff')

        today_jobs = Operationitem.objects.filter(
            company=company,
            day__date=today,
            day__operation__follow_staff=personel
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
        active_operations = None
        today_jobs = None

    context.update({
        'active_operations': active_operations,
        'today_jobs': today_jobs
    })

    create_activity_log(
        company=company,
        staff=personel,
        action="Dashboard sayfasını ziyaret etti",
        request=request
    )

    cache.set(cache_key, context, cache_timeout)
    return render(request, 'dashboard.html', context)




@login_required(login_url='tour:login')
def generic_list(request, model_name):
    """
    Generic view function that lists objects from a specified model.
    """
    model, _ = get_model_and_form(model_name)
    
    # Cache anahtarı oluştur
    cache_key = f"generic_list_{model_name}_{request.user.id}"
    cache_timeout = 60  # 1 dakika

    # Arama sorgusu
    query = request.GET.get('q')

    # Eğer arama yapılmıyorsa cache'den veri getirmeyi dene
    if not query:
        cached_data = cache.get(cache_key)
        if cached_data:
            create_activity_log(
                company=None,
                staff=None,
                action=f"{model._meta.verbose_name_plural} listesini ziyaret etti",
                request=request
            )
            return render(request, 'generic/list.html', cached_data)

    # Queryset oluştur
    queryset = get_filtered_queryset(model, request)
    
    # select_related ekle
    select_related_fields = get_select_related_fields(model_name)
    if select_related_fields:
        queryset = queryset.select_related(*select_related_fields)

    # Veritabanından veriyi al
    objects = list(queryset)

    # Context oluştur
    context = {
        'objects': objects,
        'model_name': model_name,
        'model_verbose_name': model._meta.verbose_name,
        'model_verbose_name_plural': model._meta.verbose_name_plural,
        'query': query,
    }

    # Log kaydı oluştur
    create_activity_log(
        company=None,
        staff=None,
        action=f"{model._meta.verbose_name_plural} listesini ziyaret etti",
        request=request
    )

    # Önbelleğe al (sadece arama yapılmıyorsa)
    if not query:
        cache.set(cache_key, context, cache_timeout)

    return render(request, 'generic/list.html', context)

@login_required(login_url='tour:login')
def generic_create(request, model_name):
    """
    Generic view function for creating objects of a specified model.
    """
    model, form_class = get_model_and_form(model_name)
    
    # Kullanıcı şirket bilgisi al
    personel, company = get_user_company_info(request.user)
    if not company and request.user.is_superuser:
        company = Sirket.objects.get(id=1)

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            # Personel formu özel işlem gerektiriyor
            if model_name.lower() == 'personel':
                instance = form.save(commit=True, company=company)
            else:
                instance = form.save(commit=False)
                if hasattr(model, 'company') and company:
                    instance.company = company
                instance.save()

            # Log kaydı oluştur
            log_details = get_object_details(instance)
            create_activity_log(
                company=company,
                staff=personel,
                action=f"{model._meta.verbose_name} oluşturdu. Detaylar: {log_details}",
                request=request
            )

            messages.success(request, f"{model._meta.verbose_name} başarıyla oluşturuldu.")
            return redirect('tour:' + model_name.lower() + '_list')
    else:
        form = form_class()

    context = {
        'form': form,
        'model_name': model_name,
        'model_verbose_name': model._meta.verbose_name,
        'form_action': 'Oluştur',
        'is_create': True
    }

    return render(request, 'generic/form.html', context)

@login_required(login_url='tour:login')
def generic_update(request, model_name, pk):
    """
    Generic view function that updates an object from a specified model.
    """
    model, form_class = get_model_and_form(model_name)
    
    try:
        obj = get_object_or_404(model, pk=pk)
    except:
        messages.error(request, f"{model._meta.verbose_name} bulunamadı.")
        return redirect('tour:' + model_name.lower() + '_list')

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            # Değişiklikten önce mevcut veriyi kaydet
            old_data = get_object_details(obj)
            
            # Formu kaydet
            updated_instance = form.save()
            
            # Log kaydı oluştur
            new_data = get_object_details(updated_instance)
            personel, company = get_user_company_info(request.user)
            
            create_activity_log(
                company=company,
                staff=personel,
                action=f"{model._meta.verbose_name} güncelledi. Detaylar: {old_data} -> {new_data}",
                request=request
            )

            messages.success(request, f"{model._meta.verbose_name} başarıyla güncellendi.")
            return redirect('tour:' + model_name.lower() + '_list')
    else:
        form = form_class(instance=obj)

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
    """
    model, _ = get_model_and_form(model_name)
    
    try:
        obj = get_object_or_404(model, pk=pk)
    except:
        messages.error(request, f"{model._meta.verbose_name} bulunamadı.")
        return redirect('tour:' + model_name.lower() + '_list')

    try:
        # Silme işleminden önce nesne detaylarını kaydet
        log_details = get_object_details(obj)
        personel, company = get_user_company_info(request.user)

        if hasattr(obj, 'is_delete'):
            obj.is_delete = True
            obj.save()
            messages.success(request, f"{model._meta.verbose_name} başarıyla silindi.")
            
            create_activity_log(
                company=company,
                staff=personel,
                action=f"{model._meta.verbose_name} sildi. Detaylar: {log_details}",
                request=request
            )
        else:
            obj.delete()
            messages.success(request, f"{model._meta.verbose_name} başarıyla silindi.")
            
            create_activity_log(
                company=company,
                staff=personel,
                action=f"{model._meta.verbose_name} kalıcı olarak sildi. Detaylar: {log_details}",
                request=request
            )
    except Exception as e:
        messages.error(request, f"Hata oluştu: {str(e)}")

    return redirect('tour:' + model_name.lower() + '_list')

@login_required(login_url='tour:login')
def generic_deleted_list(request, model_name):
    """
    Generic view function that lists deleted objects.
    """
    model, _ = get_model_and_form(model_name)
    
    # Queryset oluştur
    queryset = get_filtered_queryset(model, request, is_deleted=True)

    context = {
        'objects': queryset,
        'model_name': model_name,
        'model_verbose_name': model._meta.verbose_name,
        'model_verbose_name_plural': model._meta.verbose_name_plural,
        'query': request.GET.get('q'),
        'is_deleted_list': True,
    }

    # Log kaydı oluştur
    personel, company = get_user_company_info(request.user)
    create_activity_log(
        company=company,
        staff=personel,
        action=f"Silinmiş {model._meta.verbose_name_plural} listesini ziyaret etti",
        request=request
    )

    return render(request, 'generic/deleted_list.html', context)

@login_required(login_url='tour:login')
def restore_object(request, model_name, pk):
    """
    Generic view function that restores a deleted object.
    """
    model, _ = get_model_and_form(model_name)
    
    try:
        obj = get_object_or_404(model, pk=pk, is_delete=True)
    except:
        messages.error(request, f"Silinmiş {model._meta.verbose_name} bulunamadı.")
        return redirect('tour:' + model_name.lower() + '_deleted_list')

    try:
        # Geri getirme işleminden önce nesne detaylarını kaydet
        log_details = get_object_details(obj)
        personel, company = get_user_company_info(request.user)

        obj.is_delete = False
        obj.save()

        create_activity_log(
            company=company,
            staff=personel,
            action=f"{model._meta.verbose_name} geri getirdi. Detaylar: {log_details}",
            request=request
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
        # Temel sorguyu oluştur
        base_query = get_base_activity_log_query()
        
        # Kullanıcı tipine göre logları filtrele
        user_activity_logs, title, error_message = get_user_activity_logs(request, base_query)
        
        # Hata mesajı varsa göster
        if error_message:
            messages.warning(request, error_message)
        
        # Sorgu sonuçlarını değerlendir
        if not user_activity_logs.exists():
            messages.info(request, "GÖRÜNTÜLENECEK AKTİVİTE KAYDI BULUNAMADI")

        # Toplam kayıt sayısını hesapla
        total_count = user_activity_logs.count()

        # Sayfalama için kayıtları al
        page = request.GET.get('page', 1)
        logs = paginate_activity_logs(user_activity_logs, page)

        context = {
            'page_title': title,
            'logs': logs,
            'is_activity_log': True,
            'filtre_tarih': (timezone.now() - timezone.timedelta(days=3)).strftime('%d.%m.%Y'),
            'total_count': total_count
        }

        return render(request, 'generic/activity_logs.html', context)

    except Exception as e:
        logger.error(f"Aktivite log hatası: {str(e)}", exc_info=True)
        messages.error(request, f"AKTİVİTE KAYITLARI GÖRÜNTÜLENİRKEN HATA OLUŞTU: {str(e)}")
        return redirect('tour:dashboard')



@login_required(login_url='tour:login')
def operation_create(request):
    """
    Yeni bir operasyon oluşturmak için view fonksiyonu
    """
    # Kullanıcı şirket bilgisi al
    personel, company = get_user_company_info(request.user)
    if not company and request.user.is_superuser:
        company = Sirket.objects.get(id=1)

    if request.method == 'POST':
        form = OperationForm(request.POST, company=company)
        if form.is_valid():
            try:
                # Formu kaydet ve günleri oluştur
                instance, days = save_operation_form(form, company, personel)
                
                # Log kaydı oluştur
                log_message = get_operation_log_message(instance, request.user.is_superuser)
                create_activity_log(
                    company=company,
                    staff=personel,
                    action=log_message,
                    request=request
                )

                messages.success(request, f"Operasyon başarıyla oluşturuldu: {instance.ticket} (#{instance.buyer_company.name})")
                return redirect('tour:operation_detail', pk=instance.id)
                
            except Exception as e:
                logger.error(f"Operasyon oluşturma hatası: {str(e)}")
                messages.error(request, f"Operasyon oluşturulurken bir hata oluştu: {str(e)}")
    else:
        form = OperationForm(company=company)

    return render(request, 'operation/create.html', {'form': form})



@login_required(login_url='tour:login')
def operation_detail(request, pk):
    """
    Operasyon detaylarını görüntülemek için view fonksiyonu.
    Performans için gerekli tüm öğeler önceden alınır ve ilişkisel sorgular optimize edilir.
    """

    try:
        # Operasyonu ve ilişkili verileri getir
        operation = get_operation_with_relations(pk)
        days, items, items_by_day = get_operation_detail_data(operation)

        # Log kaydı oluştur
        log_message = get_operation_detail_log_message(operation, request.user.is_superuser)
        personel, company = get_user_company_info(request.user)
        create_activity_log(
            company=company,
            staff=personel,
            action=log_message,
            request=request
        )

        # Context oluştur
        context = {
            'operation': operation,
            'days': days,
            'items': items,
            'items_by_day': items_by_day,
        }


        return render(request, 'operation/detail.html', context)

    except Exception as e:
        logger.error(f"Operasyon detay görüntüleme hatası: {str(e)}")
        messages.error(request, f"Operasyon detayları görüntülenirken bir hata oluştu: {str(e)}")
        return redirect('tour:dashboard')



@login_required(login_url='tour:login')
def operation_edit(request, pk):
    """
    Operasyon düzenleme view fonksiyonu.
    """
    try:
        # Operasyonu getir
        operation = get_object_or_404(Operation, pk=pk)
        
        # Kullanıcı bilgilerini al
        personel, company = get_user_company_info(request.user)
        
        if request.method == 'POST':
            form = OperationForm(request.POST, instance=operation)
            
            # Formu kaydet
            success, instance, error = save_operation_edit_form(form, operation, company, personel)
            
            if success:
                # Başarılı log kaydı
                log_message = get_operation_edit_log_message(
                    operation=operation,
                    action_type='create',
                    is_superuser=request.user.is_superuser
                )
                create_activity_log(
                    company=company,
                    staff=personel,
                    action=log_message,
                    request=request
                )
                return render(request, 'operation/partials/operation-card.html', {'operation': operation})
            else:
                # Hata log kaydı
                log_message = get_operation_edit_log_message(
                    operation=operation,
                    action_type='error',
                    is_superuser=request.user.is_superuser,
                    form_errors=error
                )
                create_activity_log(
                    company=company,
                    staff=personel,
                    action=log_message,
                    request=request
                )
                logger.error(f"Form hataları: {error}")
        else:
            form = OperationForm(instance=operation)
            
            # Sayfa ziyaret log kaydı
            log_message = get_operation_edit_log_message(
                operation=operation,
                action_type='visit',
                is_superuser=request.user.is_superuser
            )
            create_activity_log(
                company=company,
                staff=personel,
                action=log_message,
                request=request
            )

        return render(request, 'operation/edit.html', {'form': form, 'operation': operation})
        
    except Exception as e:
        logger.error(f"Operasyon düzenleme hatası: {str(e)}")
        messages.error(request, f"Operasyon düzenlenirken bir hata oluştu: {str(e)}")
        return redirect('tour:dashboard')



@login_required(login_url='tour:login')
def operationitem_edit(request, pk):
    """
    Operasyon öğesi düzenleme view fonksiyonu.
    """
    try:
        # Operasyon öğesini getir
        item = get_object_or_404(Operationitem, pk=pk)
        
        # Eski değerleri kaydet
        old_driver = item.driver
        old_driver_phone = item.driver_phone if item.driver else None
        old_guide = item.guide
        old_guide_phone = item.guide.phone if item.guide else None
        
        form = OperationItemForm(request.POST or None, instance=item)
        
        if request.method == 'POST':
            if form.is_valid():
                # Formu kaydet
                new_item = form.save(commit=False)
                
                # Araç fiyatını hesapla
                new_item.vehicle_price = calculate_vehicle_price(new_item)
                
                # Aktivite fiyatını güncelle
                if new_item.activity and new_item.manuel_activity_price and new_item.activity_price == 0:
                    new_item.activity_price = new_item.manuel_activity_price
                
                new_item.save()
                
                # SMS gönder
                send_operation_sms(new_item, old_driver, old_guide)
                
                return render(request, 'operation/partials/item-table.html', {'item': new_item})
            else:
                logger.error(f"Form hataları: {form.errors}")
                
        return render(request, 'operation/item-edit.html', {'form': form, 'item': item})
        
    except Exception as e:
        logger.error(f"Operasyon öğesi düzenleme hatası: {str(e)}")
        messages.error(request, f"Operasyon öğesi düzenlenirken bir hata oluştu: {str(e)}")
        return redirect('tour:dashboard')


@login_required(login_url='tour:login')
def operation_toggle_view(request, pk):
    """
    Operasyonu ve ilişkili tüm öğeleri siler/geri yükler.
    """
    try:
        # Operasyonu getir
        operation = get_object_or_404(Operation, pk=pk)
        
        # Silme/geri yükleme işlemini gerçekleştir
        success, error, is_deleted = toggle_operation(operation)
        
        if success:
            # Log kaydı oluştur
            personel, company = get_user_company_info(request.user)
            create_activity_log(
                company=company,
                staff=personel,
                action=get_operation_toggle_log_message(operation, is_deleted, request.user.is_superuser),
                request=request
            )
            messages.success(request, f"Operasyon başarıyla {'geri yüklendi' if is_deleted else 'silindi'}.")
        else:
            messages.error(request, f"Operasyon {'geri yüklenirken' if is_deleted else 'silinirken'} bir hata oluştu: {error}")
            
        next_url = request.GET.get('next')
        return redirect(next_url if next_url else 'tour:operation_list')
        
    except Exception as e:
        logger.error(f"Operasyon {'geri yükleme' if operation.is_delete else 'silme'} hatası: {str(e)}")
        messages.error(request, f"Operasyon {'geri yüklenirken' if operation.is_delete else 'silinirken'} bir hata oluştu: {str(e)}")
        return redirect('tour:operation_list')


@login_required(login_url='tour:login')
def operationday_toggle_view(request, pk):
    """
    Operasyon gününü ve ilişkili öğeleri siler/geri yükler.
    """
    try:
        # Operasyon gününü getir
        day = get_object_or_404(Operationday, pk=pk)
        
        # Silme/geri yükleme işlemini gerçekleştir
        success, error, is_deleted = toggle_operation_day(day)
        
        if success:
            # Log kaydı oluştur
            personel, company = get_user_company_info(request.user)
            create_activity_log(
                company=company,
                staff=personel,
                action=get_operation_day_toggle_log_message(day, is_deleted, request.user.is_superuser),
                request=request
            )
            messages.success(request, f"Operasyon günü başarıyla {'geri yüklendi' if is_deleted else 'silindi'}.")
        else:
            messages.error(request, f"Operasyon günü {'geri yüklenirken' if is_deleted else 'silinirken'} bir hata oluştu: {error}")
            
        next_url = request.GET.get('next')
        return redirect(next_url if next_url else 'tour:operation_list')
        
    except Exception as e:
        logger.error(f"Operasyon günü {'geri yükleme' if day.is_delete else 'silme'} hatası: {str(e)}")
        messages.error(request, f"Operasyon günü {'geri yüklenirken' if day.is_delete else 'silinirken'} bir hata oluştu: {str(e)}")
        return redirect('tour:operation_list')



@login_required(login_url='tour:login')
def operationitem_toggle_view(request, pk):
    """
    Operasyon öğesini siler/geri yükler.
    """
    try:
        # Operasyon öğesini getir
        item = get_object_or_404(Operationitem, pk=pk)
        
        # Silme/geri yükleme işlemini gerçekleştir
        success, error, is_deleted = toggle_operation_item(item)
        
        if success:
            # Log kaydı oluştur
            personel, company = get_user_company_info(request.user)
            create_activity_log(
                company=company,
                staff=personel,
                action=get_operation_item_toggle_log_message(item, is_deleted, request.user.is_superuser),
                request=request
            )
            messages.success(request, f"Operasyon öğesi başarıyla {'geri yüklendi' if is_deleted else 'silindi'}.")
        else:
            messages.error(request, f"Operasyon öğesi {'geri yüklenirken' if is_deleted else 'silinirken'} bir hata oluştu: {error}")
            
        next_url = request.GET.get('next')
        return redirect(next_url if next_url else 'tour:operation_detail', pk=item.day.operation.id)
        
    except Exception as e:
        logger.error(f"Operasyon öğesi {'geri yükleme' if item.is_delete else 'silme'} hatası: {str(e)}")
        messages.error(request, f"Operasyon öğesi {'geri yüklenirken' if item.is_delete else 'silinirken'} bir hata oluştu: {str(e)}")
        return redirect('tour:dashboard')
    

@login_required(login_url='tour:login')
def operation_deleted_list(request):
    """
    Operasyonları aylara, yıllara ve diğer kriterlere göre listeleyen view fonksiyonu.
    Performans optimizasyonu yapılmış versiyonu.
    """
    try:
        # Kullanıcı ve şirket bilgilerini al
        staff, company = get_user_company_info(request.user)
        
        # Temel sorgu yapısını oluştur
        base_query = Operation.objects.select_related(
            'company',
            'buyer_company',
            'selling_staff',
            'selling_staff__user',
            'follow_staff',
            'follow_staff__user'
        ).filter(is_delete=True)
        
        # Şirket filtrelemesi
        if company:
            base_query = base_query.filter(company=company)
            
        # Filtreleri uygula
        filters, month, year, current_filters = get_operation_list_filters(request, company)
        queryset = base_query.filter(filters).order_by('-start')
        
        # İstatistikleri hesapla
        stats = get_operation_list_stats(queryset)
        
        # Yıl listesini al
        year_list = get_operation_list_year_list()
        
        # Müşteri şirketlerini ve personel listesini al
        companies = Buyercompany.objects.filter(
            is_delete=False,
            **({"company": company} if company else {})
        ).only('id', 'name')
        
        staffs = Personel.objects.filter(
            is_active=True,
            **({"company": company} if company else {})
        ).select_related('user').only('id', 'user__first_name', 'user__last_name')
        
        # Log kaydı oluştur
        create_activity_log(
            request=request,
            company=company,
            staff=staff,
            action="Operasyon listesini görüntüledi"
        )
        
        # Sonuçları sayfalama
        paginator = Paginator(queryset, 50)
        page = request.GET.get('page')
        try:
            operations = paginator.page(page)
        except PageNotAnInteger:
            operations = paginator.page(1)
        except EmptyPage:
            operations = paginator.page(paginator.num_pages)
            
        # Context oluştur
        context = get_operation_list_context(
            operations, month, year, year_list,
            companies, staffs, stats, current_filters
        )
        
        return render(request, 'operation/list.html', context)
        
    except Exception as e:
        logger.error(f"Operasyon listesi hatası: {str(e)}", exc_info=True)
        messages.error(request, f"OPERASYON LİSTESİ GÖRÜNTÜLENİRKEN HATA OLUŞTU: {str(e)}")
        return redirect('tour:dashboard')


@login_required(login_url='tour:login')
def operationday_item_create(request, day_id):
    """
    Operasyon günü öğesi oluşturma view fonksiyonu.
    """
    try:
        day = get_object_or_404(Operationday, id=day_id)
        staff, company = get_user_company_info(request.user)
        
        if request.method == 'POST':
            form = OperationItemForm(request.POST, company=company)
            success, item, error = save_operation_day_item(form, day, company)
            
            if success:
                # Log kaydı oluştur
                create_activity_log(
                    request=request,
                    company=company,
                    staff=staff,
                    action=get_operation_day_log_message(day, 'create', item=item)
                )
                return render(request, 'operation/partials/item-table.html', {'item': item})
            else:
                # Hata log kaydı oluştur
                create_activity_log(
                    request=request,
                    company=company,
                    staff=staff,
                    action=get_operation_day_log_message(day, 'error', item=item, form_errors=error)
                )
                logger.error(f"Form hataları: {error}")
        else:
            form = OperationItemForm(company=company)
            # Ziyaret log kaydı oluştur
            create_activity_log(
                request=request,
                company=company,
                staff=staff,
                action=get_operation_day_log_message(day, 'visit')
            )
            
        return render(request, 'operation/partials/item-create.html', {'form': form, 'day': day})
        
    except Exception as e:
        logger.error(f"Operasyon günü öğesi oluşturma hatası: {str(e)}")
        messages.error(request, f"Operasyon günü öğesi oluşturulurken bir hata oluştu: {str(e)}")
        return redirect('tour:dashboard')



@login_required(login_url='tour:login')
def operation_list(request):
    """
    Operasyonları aylara, yıllara ve diğer kriterlere göre listeleyen view fonksiyonu.
    Performans optimizasyonu yapılmış versiyonu.
    """
    try:
        # Kullanıcı ve şirket bilgilerini al
        staff, company = get_user_company_info(request.user)
        
        # Temel sorgu yapısını oluştur
        base_query = Operation.objects.select_related(
            'company',
            'buyer_company',
            'selling_staff',
            'selling_staff__user',
            'follow_staff',
            'follow_staff__user'
        ).filter(is_delete=False)
        
        # Şirket filtrelemesi
        if company:
            base_query = base_query.filter(company=company)
            
        # Filtreleri uygula
        filters, month, year, current_filters = get_operation_list_filters(request, company)
        queryset = base_query.filter(filters).order_by('-start')
        
        # İstatistikleri hesapla
        stats = get_operation_list_stats(queryset)
        
        # Yıl listesini al
        year_list = get_operation_list_year_list()
        
        # Müşteri şirketlerini ve personel listesini al
        companies = Buyercompany.objects.filter(
            is_delete=False,
            **({"company": company} if company else {})
        ).only('id', 'name')
        
        staffs = Personel.objects.filter(
            is_active=True,
            **({"company": company} if company else {})
        ).select_related('user').only('id', 'user__first_name', 'user__last_name')
        
        # Log kaydı oluştur
        create_activity_log(
            request=request,
            company=company,
            staff=staff,
            action="Operasyon listesini görüntüledi"
        )
        
        # Sonuçları sayfalama
        paginator = Paginator(queryset, 50)
        page = request.GET.get('page')
        try:
            operations = paginator.page(page)
        except PageNotAnInteger:
            operations = paginator.page(1)
        except EmptyPage:
            operations = paginator.page(paginator.num_pages)
            
        # Context oluştur
        context = get_operation_list_context(
            operations, month, year, year_list,
            companies, staffs, stats, current_filters
        )
        
        return render(request, 'operation/list.html', context)
        
    except Exception as e:
        logger.error(f"Operasyon listesi hatası: {str(e)}", exc_info=True)
        messages.error(request, f"OPERASYON LİSTESİ GÖRÜNTÜLENİRKEN HATA OLUŞTU: {str(e)}")
        return redirect('tour:dashboard')




@login_required(login_url='tour:login')
def job_list(request):
    try:
        # Tarihleri hesapla
        today, tomorrow, nextday, dates = get_job_list_dates()
        
        # Kullanıcı ve şirket bilgilerini al
        staff, company = get_user_company_info(request.user)
        
        # Temel sorguyu oluştur
        base_query = get_job_list_base_query(dates, company)
        
        # Tüm öğeleri tek sorguda al ve hafızada grupla
        all_items = base_query
        
        # Sonuçları hafızada grupla
        items_by_date = {date: [] for date in dates}
        for item in all_items:
            items_by_date[item.day.date].append(item)
            
        # Log kaydını oluştur
        create_job_list_log(request, company, staff)
        
        # Tarih araması için değişkenler
        search_date = None
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            # Tarih araması yap
            search_date = get_job_list_search_query(start_date, end_date, company)
            
            if not search_date.exists():
                messages.warning(request, "SEÇİLEN TARİH ARALIĞINDA GÖREV BULUNAMADI!")
                search_date = None
            elif staff:
                create_job_list_log(request, company, staff, True, start_date, end_date)
                
        # Context oluştur
        context = get_job_list_context(today, tomorrow, nextday, items_by_date, search_date)
        
        return render(request, 'job/list.html', context)
        
    except Exception as e:
        messages.error(request, f"İŞ LİSTESİ GÖRÜNTÜLENIRKEN HATA OLUŞTU: {str(e)}")
        return redirect('tour:dashboard')

@login_required(login_url='tour:login')
def my_job_list(request):
    try:
        # Tarihleri hesapla
        today, tomorrow, nextday, dates = get_job_list_dates()
        
        # Kullanıcı ve şirket bilgilerini al
        staff, company = get_user_company_info(request.user)
        
        # Temel sorguyu oluştur
        base_query = get_job_list_base_query(dates, company, staff)
        
        # Tüm öğeleri tek sorguda al ve hafızada grupla
        all_items = base_query
        
        # Sonuçları hafızada grupla
        items_by_date = {date: [] for date in dates}
        for item in all_items:
            items_by_date[item.day.date].append(item)
            
        # Log kaydını oluştur
        create_job_list_log(request, company, staff)
        
        # Tarih araması için değişkenler
        search_date = None
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                # Tarih araması yap
                search_date = get_job_list_search_query(start_date, end_date, company, staff)
                
                if search_date and search_date.exists():
                    create_job_list_log(request, company, staff, True, start_date, end_date)
                else:
                    messages.warning(request, "SEÇİLEN TARİH ARALIĞINDA GÖREV BULUNAMADI!")
                    search_date = None
            except Exception as e:
                messages.error(request, f"TARİH ARAMASINDA HATA OLUŞTU: {str(e)}")
                search_date = None
                
        # Context oluştur
        context = get_job_list_context(today, tomorrow, nextday, items_by_date, search_date)
        
        return render(request, 'job/list.html', context)
        
    except Exception as e:
        messages.error(request, f"İŞ LİSTESİ GÖRÜNTÜLENIRKEN HATA OLUŞTU: {str(e)}")
        return redirect('tour:dashboard')
    
@login_required(login_url='tour:login')
def operationitemfile_create(request, pk):
    try:
        operation_item = get_object_or_404(Operationitem, pk=pk)
        operation = operation_item.day.operation
        
        if request.method == 'POST':
            form = OperationFileForm(request.POST, request.FILES)
            success, file, error = save_operation_file_form(form, operation, operation_item)
            
            if success:
                return render(request, get_operation_file_partial_template(operation_item), 
                            get_operation_file_context_data(operation_item))
            else:
                messages.error(request, f"Dosya yüklenirken hata oluştu: {error}")
        else:
            form = OperationFileForm()
            
        return render(request, get_operation_file_template(operation_item), 
                     get_operation_file_context(form, operation, operation_item))
                     
    except Exception as e:
        messages.error(request, f"Dosya yükleme işlemi sırasında hata oluştu: {str(e)}")
        return redirect('tour:dashboard')

@login_required(login_url='tour:login')
def operationfile_create(request, pk):
    try:
        operation = get_object_or_404(Operation, pk=pk)
        
        if request.method == 'POST':
            form = OperationFileForm(request.POST, request.FILES)
            success, file, error = save_operation_file_form(form, operation)
            
            if success:
                return render(request, get_operation_file_partial_template(), 
                            get_operation_file_context_data())
            else:
                messages.error(request, f"Dosya yüklenirken hata oluştu: {error}")
        else:
            form = OperationFileForm()
            
        return render(request, get_operation_file_template(), 
                     get_operation_file_context(form, operation))
                     
    except Exception as e:
        messages.error(request, f"Dosya yükleme işlemi sırasında hata oluştu: {str(e)}")
        return redirect('tour:dashboard')


def cost_calculate():
    """
    Araç maliyetlerini hesaplar.
    """
    try:
        items = Operationitem.objects.all()
        update_item_costs(items, days_back=1, include_activity=False)
    except Exception as e:
        logger.error(f"Araç maliyeti hesaplama hatası: {str(e)}")

def activity_cost_calculate():
    """
    Aktivite maliyetlerini hesaplar.
    """
    try:
        items = Operationitem.objects.filter(activity__isnull=False)
        update_item_costs(items, days_back=3, include_activity=True)
    except Exception as e:
        logger.error(f"Aktivite maliyeti hesaplama hatası: {str(e)}")

@login_required
def operationitem_deleted_list(request, operation_id):
    """Silinmiş operasyon öğelerini listeler"""
    operation = get_object_or_404(Operation, pk=operation_id)   
    try:
        # Temel sorguyu oluştur
        query = get_deleted_items_query(
            company=request.user.company if not request.user.is_superuser else None,
            staff=request.user if not request.user.is_superuser else None
        ).filter(
            day__operation=operation,  # Sadece seçilen operasyona ait öğeleri filtrele
            is_delete=True  # Sadece silinmiş öğeleri filtrele
        )
        
        # Arama parametrelerini al
        search_params = {
            'query': request.GET.get('q'),
            'start_date': request.GET.get('start_date'),
            'end_date': request.GET.get('end_date')
        }
        
        # Filtreleri uygula
        query = apply_item_filters(query, search_params)
        
        # Sayfalama
        paginator = Paginator(query, 10)  # Her sayfada 10 öğe
        page = request.GET.get('page', 1)
        items = paginator.get_page(page)
        
        # Aktivite logu oluştur
        personel, company = get_user_company_info(request.user)
        create_activity_log(
            request=request,
            company=company,
            staff=personel,
            action=f"Operasyon #{operation.id} için silinmiş öğeler listelendi"
        )
        
        context = {
            'items': items,
            'query': search_params['query'],
            'start_date': search_params['start_date'],
            'end_date': search_params['end_date'],
            'total_count': query.count(),
            'operation': operation
        }
        
        return render(request, 'operation/deleted_items.html', context)
        
    except Exception as e:
        logger.error(f"Silinmiş operasyon öğeleri listelenirken hata oluştu: {str(e)}")
        messages.error(request, f"Silinmiş operasyon öğeleri listelenirken bir hata oluştu: {str(e)}")
        return redirect('tour:operation_detail', pk=operation_id)