import re
import requests
import random
import logging
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db.models import Q
from tour.models import *
from tour.forms import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from django.db.models.functions import ExtractYear

logger = logging.getLogger(__name__)

# Model ve form eşleştirmeleri
MODEL_MAP = {
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

FORM_MAP = {
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

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_company_info(user):
    """
    Kullanıcının personel ve şirket bilgilerini döndürür.
    
    Args:
        user: Django User modeli instance'ı
        
    Returns:
        tuple: (personel, company) veya (None, None)
    """
    if hasattr(user, 'personel') and user.personel.exists():
        personel = user.personel.first()
        return personel, personel.company
    return None, None

def normalize_phone_number(phone=None):
    if phone is None:
        return None

    digits = re.sub(r'\D', '', phone)

    if len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    if len(digits) == 12 and digits.startswith('90'):
        digits = digits[2:]

    return digits if len(digits) == 10 and digits.startswith('5') else None

def send_sms(phone, message):
    url = "https://api.netgsm.com.tr/sms/send/xml"
    headers = {'Content-Type': 'application/xml'}
    usercode = "8503081334"
    password = "F#D6C7B"
    appkey = "xxxx"

    try:
        response = requests.get('https://api.ipify.org?format=json')
        logger.info(f"Sunucu IP: {response.json()['ip']}")
    except:
        logger.error("IP adresi alınamadı")

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
               <mp><msg><![CDATA[{message}]]></msg><no>{phone}</no></mp>
           </body>
        </mainbody>"""

    try:
        response = requests.post(url, data=body, headers=headers)
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.text}")
        response.raise_for_status()
        return True, "SMS başarıyla gönderildi"
    except requests.exceptions.RequestException as e:
        logger.error(f"SMS gönderimi sırasında hata oluştu: {e}")
        return False, f"SMS gönderilemedi: {str(e)}"

def generate_sms_code():
    return str(random.randint(100000, 999999))

def validate_password(request, new_password, confirm_password):
    if new_password != confirm_password:
        messages.error(request, 'Şifreler eşleşmiyor!')
        return False

    if len(new_password) < 8:
        messages.error(request, 'Şifre en az 8 karakter olmalıdır!')
        return False

    if not any(char.isdigit() for char in new_password):
        messages.error(request, 'Şifre en az bir rakam içermelidir!')
        return False

    if not any(char.isupper() for char in new_password):
        messages.error(request, 'Şifre en az bir büyük harf içermelidir!')
        return False

    return True

def create_activity_log(company=None, staff=None, action="", request=None):
    """Kullanıcı aktivite logu oluşturur"""
    log_data = {
        'action': action,
    }
    
    if company:
        log_data['company'] = company
    if staff:
        log_data['staff'] = staff
    if request:
        log_data['ip_address'] = get_client_ip(request)
        log_data['browser_info'] = request.META.get('HTTP_USER_AGENT', '')
        
    return UserActivityLog.objects.create(**log_data)

def get_model_and_form(model_name):
    """
    Model adına göre model ve form sınıflarını döndürür.
    """
    model_name = model_name.lower()
    if model_name not in MODEL_MAP:
        raise Http404(f"Model '{model_name}' bulunamadı")
    return MODEL_MAP[model_name], FORM_MAP[model_name]

def get_model_fields_for_search(model):
    """
    Model için arama yapılabilecek alanları döndürür.
    """
    return [field.name for field in model._meta.fields 
            if field.get_internal_type() in ['CharField', 'TextField']]

def get_object_details(obj, exclude_fields=None):
    """
    Nesnenin detaylarını string olarak döndürür.
    """
    if exclude_fields is None:
        exclude_fields = ['id', 'created_at', 'updated_at', 'is_delete']
        
    details = []
    for field in obj._meta.fields:
        if field.name not in exclude_fields:
            field_value = getattr(obj, field.name)
            if field_value is not None:
                details.append(f"{field.verbose_name}: {field_value}")
    return ", ".join(details)

def get_select_related_fields(model_name):
    """
    Model için select_related alanlarını döndürür.
    """
    fields = []
    
    if model_name in ['tour', 'transfer', 'vehicle', 'activity', 'museum', 
                     'supplier', 'activitysupplier', 'buyercompany', 'personel']:
        fields.append('company')
        
    if model_name == 'personel':
        fields.append('user')
        
    if model_name == 'cost':
        fields.extend(['company', 'supplier', 'tour', 'transfer'])
        
    if model_name == 'activitycost':
        fields.extend(['company', 'supplier', 'activity'])
        
    return fields

def get_filtered_queryset(model, request, is_deleted=False):
    """
    Kullanıcı ve arama kriterlerine göre filtrelenmiş queryset döndürür.
    """
    personel, company = get_user_company_info(request.user)
    query = request.GET.get('q')
    
    # Temel queryset
    base_queryset = model.objects.filter(is_delete=is_deleted)
    
    # Şirket filtresi
    if company and not request.user.is_superuser:
        base_queryset = base_queryset.filter(company=company)
    
    # Arama filtresi
    if query:
        search_fields = get_model_fields_for_search(model)
        if search_fields:
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            base_queryset = base_queryset.filter(q_objects)
    
    return base_queryset 

def get_base_activity_log_query(days=3):
    """
    Temel aktivite log sorgusunu oluşturur.
    
    Args:
        days: Kaç günlük kayıtların getirileceği
        
    Returns:
        QuerySet: Filtrelenmiş ve optimize edilmiş aktivite log sorgusu
    """
    son_gun = timezone.now() - timezone.timedelta(days=days)
    
    return UserActivityLog.objects.select_related(
        'company',
        'staff',
        'staff__user'
    ).filter(
        timestamp__gte=son_gun
    ).only(
        'action',
        'timestamp',
        'ip_address',
        'browser_info',
        'company__name',
        'staff__user__first_name',
        'staff__user__last_name'
    )

def get_user_activity_logs(request, base_query):
    """
    Kullanıcı tipine göre aktivite loglarını filtreler.
    
    Args:
        request: Django HTTP request
        base_query: Temel aktivite log sorgusu
        
    Returns:
        tuple: (user_activity_logs, title, error_message)
    """
    title = "SON 3 GÜNLÜK KULLANICI AKTİVİTE KAYITLARIM"
    error_message = None
    
    if hasattr(request.user, 'personel') and request.user.personel.exists():
        try:
            staff = request.user.personel.select_related('company', 'user').first()
            if not staff:
                raise ValueError("Personel bilgisi bulunamadı")

            company = staff.company
            if not company:
                raise ValueError("Şirket bilgisi bulunamadı")

            user_activity_logs = base_query.filter(staff=staff)
            
            create_activity_log(
                company=company,
                staff=staff,
                action="Son 3 günlük aktivite kayıtlarını görüntüledi",
                request=request
            )
            
            return user_activity_logs, title, None
            
        except ValueError as ve:
            error_message = f"PERSONEL BİLGİSİ HATASI: {str(ve)}"
        except Exception as e:
            error_message = f"PERSONEL SORGUSUNDA HATA: {str(e)}"
            
        return UserActivityLog.objects.none(), title, error_message

    elif request.user.is_superuser:
        try:
            title = "SON 3 GÜNLÜK TÜM KULLANICI AKTİVİTE KAYITLARI"
            user_activity_logs = base_query
            
            create_activity_log(
                action="Süper kullanıcı son 3 günlük tüm aktivite kayıtlarını görüntüledi",
                request=request
            )
            
            return user_activity_logs, title, None
            
        except Exception as e:
            error_message = f"SÜPER KULLANICI SORGUSUNDA HATA: {str(e)}"
            return UserActivityLog.objects.none(), title, error_message
    
    error_message = "HESABINIZ HERHANGİ BİR ŞİRKETLE İLİŞKİLENDİRİLMEMİŞ!"
    return UserActivityLog.objects.none(), title, error_message

def paginate_activity_logs(queryset, page_number, per_page=50):
    """
    Aktivite loglarını sayfalandırır.
    
    Args:
        queryset: Aktivite log sorgusu
        page_number: Sayfa numarası
        per_page: Sayfa başına kayıt sayısı
        
    Returns:
        Page: Sayfalandırılmış aktivite logları
    """
    paginator = Paginator(queryset, per_page)
    
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

def create_operation_days(operation, company):
    """
    Operasyon için günleri oluşturur.
    
    Args:
        operation: Operation modeli instance'ı
        company: Sirket modeli instance'ı
        
    Returns:
        list: Oluşturulan Operationday nesneleri
    """
    days = []
    start = operation.start
    finish = operation.finish
    
    while start <= finish:
        day = Operationday.objects.create(
            company=company,
            operation=operation,
            date=start
        )
        days.append(day)
        start += timezone.timedelta(days=1)
        
    return days

def get_operation_log_message(instance, is_superuser=False):
    """
    Operasyon log mesajını oluşturur.
    
    Args:
        instance: Operation modeli instance'ı
        is_superuser: Süper kullanıcı mı?
        
    Returns:
        str: Log mesajı
    """
    prefix = "Süper kullanıcı " if is_superuser else ""
    return f"{prefix}Yeni operasyon oluşturdu: {instance.ticket} (#{instance.buyer_company.name})"

def save_operation_form(form, company, staff):
    """
    Operasyon formunu kaydeder ve gerekli ilişkileri kurar.
    
    Args:
        form: OperationForm instance'ı
        company: Sirket modeli instance'ı
        staff: Personel modeli instance'ı
        
    Returns:
        tuple: (instance, days)
            - instance: Kaydedilen Operation nesnesi
            - days: Oluşturulan Operationday nesneleri
    """
    instance = form.save(commit=False)
    instance.company = company
    instance.selling_staff = staff
    instance.save()
    
    days = create_operation_days(instance, company)
    
    return instance, days 

def get_operation_detail_data(operation):
    """
    Operasyon detayları için gerekli verileri getirir.
    
    Args:
        operation: Operation modeli instance'ı
        
    Returns:
        tuple: (days, items, items_by_day)
    """
    # Günleri getir
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
    
    # Öğeleri günlere göre grupla
    items_by_day = {}
    for day in days:
        items_by_day[day.id] = []
    
    for item in items:
        items_by_day[item.day.id].append(item)
        
    return days, items, items_by_day

def get_operation_detail_log_message(operation, is_superuser=False):
    """
    Operasyon detay görüntüleme log mesajını oluşturur.
    
    Args:
        operation: Operation modeli instance'ı
        is_superuser: Süper kullanıcı mı?
        
    Returns:
        str: Log mesajı
    """
    prefix = "Süper kullanıcı " if is_superuser else ""
    return f"{prefix}Operasyon detayı görüntüledi: {operation.ticket}"

def get_operation_with_relations(pk):
    """
    İlişkili modellerle birlikte operasyonu getirir.
    
    Args:
        pk: Operation modeli primary key'i
        
    Returns:
        Operation: İlişkili modellerle birlikte operasyon
    """
    return get_object_or_404(
        Operation.objects.select_related(
            'company',
            'selling_staff',
            'follow_staff',
            'buyer_company'
        ),
        pk=pk
    ) 

def get_operation_edit_log_message(operation, action_type, is_superuser=False, form_errors=None):
    """
    Operasyon düzenleme log mesajını oluşturur.
    
    Args:
        operation: Operation modeli instance'ı
        action_type: Log mesajı tipi ('create', 'error', 'visit')
        is_superuser: Süper kullanıcı mı?
        form_errors: Form hataları (varsa)
        
    Returns:
        str: Log mesajı
    """
    prefix = "Süper kullanıcı " if is_superuser else ""
    
    messages = {
        'create': f"{prefix}Operasyon gününde yeni öğe oluşturdu: {operation.ticket}",
        'error': f"{prefix}Operasyon gününde yeni öğe oluşturma sırasında hata oluştu: {operation.ticket}, Hata: {form_errors}",
        'visit': f"{prefix}Operasyon gününde yeni öğe oluşturma sayfasını ziyaret etti: {operation.ticket}"
    }
    
    return messages.get(action_type, "")

def save_operation_edit_form(form, operation, company, staff):
    """
    Operasyon düzenleme formunu kaydeder.
    
    Args:
        form: OperationForm instance'ı
        operation: Operation modeli instance'ı
        company: Sirket modeli instance'ı
        staff: Personel modeli instance'ı
        
    Returns:
        tuple: (success, instance, error_message)
    """
    try:
        if form.is_valid():
            instance = form.save()
            return True, instance, None
        return False, None, form.errors
    except Exception as e:
        logger.error(f"Operasyon düzenleme hatası: {str(e)}")
        return False, None, str(e) 

def calculate_vehicle_price(item):
    """
    Araç fiyatını hesaplar.
    
    Args:
        item: Operationitem modeli instance'ı
        
    Returns:
        float: Hesaplanan araç fiyatı
    """
    if item.manuel_vehicle_price != 0:
        return item.manuel_vehicle_price
        
    if not (item.transfer or item.tour) or not item.vehicle or not item.supplier or item.vehicle_price:
        return item.vehicle_price
        
    cost = Cost.objects.filter(
        transfer=item.transfer,
        tour=item.tour,
        supplier=item.supplier,
        is_delete=False,
        company=item.company
    ).first()
    
    if not cost:
        logger.warning("Maliyet bulunamadı")
        return item.vehicle_price
        
    vehicle_prices = {
        "BINEK": cost.car,
        "MINIVAN": cost.minivan,
        "MINIBUS": cost.minibus,
        "MIDIBUS": cost.midibus,
        "OTOBUS": cost.bus
    }
    
    return vehicle_prices.get(item.vehicle.vehicle, item.vehicle_price)

def get_sms_message(item, is_cancellation=False, is_driver_change=False, is_guide_change=False):
    """
    SMS mesajını oluşturur.
    
    Args:
        item: Operationitem modeli instance'ı
        is_cancellation: İptal mesajı mı?
        is_driver_change: Şoför değişikliği mi?
        is_guide_change: Rehber değişikliği mi?
        
    Returns:
        dict: Mesaj tiplerine göre SMS mesajları
    """
    date_str = item.day.date.strftime('%d.%m.%Y')
    
    if is_cancellation:
        return {
            'driver': f"Sayın {item.driver}. {date_str} tarihinde {item.pick_time} saatindeki işiniz iptal edildi.",
            'guide': f"Sayın {item.guide.name}. {date_str} tarihinde {item.pick_time} saatindeki işiniz iptal edildi."
        }
    
    messages = {}
    
    if item.operation_type == "Transfer":
        if all([item.transfer, item.vehicle, item.pick_time, item.supplier, 
                item.driver, item.driver_phone, item.plaka, 
                item.day.date >= timezone.now().date(), item.pick_location]):
            messages['driver'] = f"Sayın {item.driver}. {date_str} tarihinde {item.pick_time} saatinde, {item.plaka} plakalı araçla {item.pick_location} adresine Misafirlerimizle buluşmak üzere {item.transfer.route} Transfer tanımlanmıştır."
            if item.guide:
                messages['guide'] = f"Sayın {item.guide.name}. {date_str} tarihinde {item.pick_time} saatinde, {item.plaka} plakalı {item.transfer.route} Transfer tanımlanmıştır. {'Yeni ' if is_driver_change else ''}Araç Şoförü: {item.driver} Telefon: {item.driver_phone}"
    
    elif item.operation_type in ["Tur", "TurTransfer", "TransferTur"]:
        if all([item.tour, item.vehicle, item.pick_time, item.supplier, 
                item.driver, item.driver_phone, item.plaka, 
                item.day.date >= timezone.now().date(), item.pick_location]):
            messages['driver'] = f"Sayın {item.driver}. {date_str} tarihinde {item.pick_time} saatinde, {item.plaka} plakalı araçla {item.pick_location} adresine Misafirlerimizle buluşmak üzere {item.tour.route} Tur tanımlanmıştır."
            if item.guide:
                messages['guide'] = f"Sayın {item.guide.name}. {date_str} tarihinde {item.pick_time} saatinde, {item.plaka} plakalı {item.tour.route} Tur tanımlanmıştır. {'Yeni ' if is_driver_change else ''}Araç Şoförü: {item.driver} Telefon: {item.driver_phone}"
    
    elif item.operation_type == "Rehber":
        if all([item.guide, item.day.date >= timezone.now().date(), 
                item.pick_time, item.pick_location]):
            if item.tour and item.tour.route == "WALKING TUR IST":
                messages['guide'] = f"Sayın {item.guide.name}. {date_str} tarihinde {item.pick_time} saatinde, {item.pick_location} adresinde Misafirlerimizle buluşmak üzere {item.tour.route} Turu tanımlanmıştır."
            else:
                messages['guide'] = f"Sayın {item.guide.name}. {date_str} tarihinde {item.pick_time} saatinde, {item.pick_location} adresinde Misafirlerimizle buluşmak üzere Rehber olarak görev tanımlanmıştır."
    
    elif item.operation_type == "Aracli Rehber":
        if all([item.guide, item.day.date >= timezone.now().date(), 
                item.pick_time, item.pick_location]):
            messages['guide'] = f"Sayın {item.guide.name}. {date_str} tarihinde {item.pick_time} saatinde, {item.pick_location} adresine Misafirlerimizle buluşmak üzere Araçlı Rehber olarak görev tanımlanmıştır."
    
    return messages

def send_operation_sms(item, old_driver=None, old_guide=None):
    """
    Operasyon SMS'lerini gönderir.
    
    Args:
        item: Operationitem modeli instance'ı
        old_driver: Eski şoför
        old_guide: Eski rehber
    """
    # Yeni görev SMS'leri
    messages = get_sms_message(item)
    
    # Şoför değişikliği
    if old_driver and old_driver != item.driver:
        # Eski şoföre iptal mesajı
        if old_driver.phone:
            send_sms(normalize_phone_number(old_driver.phone), 
                get_sms_message(item, is_cancellation=True)['driver'])
        
        # Yeni şoföre bilgilendirme mesajı
        if 'driver' in messages and item.driver_phone:
            send_sms(normalize_phone_number(item.driver_phone), messages['driver'])
    
    # Rehber değişikliği
    if old_guide and old_guide != item.guide:
        # Eski rehbere iptal mesajı
        if old_guide.phone:
            send_sms(normalize_phone_number(old_guide.phone), 
                get_sms_message(item, is_cancellation=True)['guide'])
        
        # Yeni rehbere bilgilendirme mesajı
        if 'guide' in messages and item.guide.phone:
            send_sms(normalize_phone_number(item.guide.phone), messages['guide'])
    
    # Normal durumda SMS gönderimi
    if not old_driver and not old_guide:
        if 'driver' in messages and item.driver_phone:
            send_sms(normalize_phone_number(item.driver_phone), messages['driver'])
        if 'guide' in messages and item.guide.phone:
            send_sms(normalize_phone_number(item.guide.phone), messages['guide']) 

def get_operation_day_log_message(day, action_type, item=None, form_errors=None):
    """
    Operasyon günü log mesajını oluşturur.
    
    Args:
        day: Operationday modeli instance'ı
        action_type: Log mesajı tipi ('create', 'error', 'visit')
        item: Operationitem modeli instance'ı (varsa)
        form_errors: Form hataları (varsa)
        
    Returns:
        str: Log mesajı
    """
    messages = {
        'create': f"Operasyon gününde yeni öğe oluşturdu: {item.operation_type}",
        'error': f"Operasyon gününde yeni öğe oluşturma sırasında hata oluştu: {item.operation_type}, {day.date}, {item.id}, Hata: {form_errors}",
        'visit': f"Operasyon gününde yeni öğe oluşturma sayfasını ziyaret etti: {day.date}"
    }
    
    return messages.get(action_type, "")

def save_operation_day_item(form, day, company):
    """
    Operasyon günü öğesini kaydeder.
    
    Args:
        form: OperationItemForm instance'ı
        day: Operationday modeli instance'ı
        company: Sirket modeli instance'ı
        
    Returns:
        tuple: (success, item, error_message)
    """
    try:
        if form.is_valid():
            item = form.save(commit=False)
            item.day = day
            item.company = company
            item.save()
            form.save_m2m()  # ManyToMany ilişkilerini kaydet
            return True, item, None
        return False, None, form.errors
    except Exception as e:
        logger.error(f"Operasyon günü öğesi kaydetme hatası: {str(e)}")
        return False, None, str(e) 

def get_operation_list_filters(request, company=None):
    """
    Operasyon listesi için filtreleri oluşturur.
    
    Args:
        request: Django HTTP request
        company: Sirket modeli instance'ı (varsa)
        
    Returns:
        tuple: (filters, month, year, current_filters)
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

    # Tarih hesaplamaları
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Varsayılan değerleri ayarla
    if not any([month, ticket, buyer_company_id, selling_staff_id, follow_staff_id, start_date, end_date]):
        month = str(current_month)
        year = str(current_year)
    elif month and not year:
        year = str(current_year)

    # Filtreleri oluştur
    filters = Q()

    # Ay ve yıl filtresi
    if month and year:
        try:
            month_int = int(month)
            year_int = int(year)

            month_start = timezone.datetime(year_int, month_int, 1).date()
            if month_int == 12:
                month_end = timezone.datetime(year_int + 1, 1, 1).date() - timezone.timedelta(days=1)
            else:
                month_end = timezone.datetime(year_int, month_int + 1, 1).date() - timezone.timedelta(days=1)

            filters &= Q(start__lte=month_end) & Q(finish__gte=month_start)
        except ValueError:
            logger.error("Geçersiz ay veya yıl değeri!")

    # Diğer filtreleri ekle
    if ticket:
        filters &= Q(ticket__icontains=ticket)
    if buyer_company_id:
        filters &= Q(buyer_company_id=buyer_company_id)
    if selling_staff_id:
        filters &= Q(selling_staff_id=selling_staff_id)
    if follow_staff_id:
        filters &= Q(follow_staff_id=follow_staff_id)
    if start_date:
        filters &= Q(start__gte=start_date)
    if end_date:
        filters &= Q(finish__lte=end_date)

    current_filters = {
        'month': month,
        'year': year,
        'ticket': ticket,
        'buyer_company_id': buyer_company_id,
        'selling_staff_id': selling_staff_id,
        'follow_staff_id': follow_staff_id,
        'start_date': start_date,
        'end_date': end_date
    }

    return filters, month, year, current_filters

def get_operation_list_stats(queryset):
    """
    Operasyon listesi için istatistikleri hesaplar.
    
    Args:
        queryset: Operation queryset'i
        
    Returns:
        dict: İstatistik bilgileri
    """
    today = timezone.now().date()
    return {
        'completed_count': queryset.filter(finish__lt=today).count(),
        'active_count': queryset.filter(start__lte=today, finish__gte=today).count(),
        'upcoming_count': queryset.filter(start__gt=today).count()
    }

def get_operation_list_year_list():
    """
    Operasyon listesi için yıl listesini oluşturur.
    
    Returns:
        list: Yıl listesi
    """
    year_list = Operation.objects.filter(
        is_delete=False
    ).annotate(
        year=ExtractYear('start')
    ).values_list(
        'year', flat=True
    ).distinct().order_by('year')

    year_list = sorted(set(year for year in year_list if year is not None))
    
    if not year_list:
        year_list = [timezone.now().year]
        
    return year_list

def get_operation_list_context(operations, month, year, year_list, companies, staffs, stats, current_filters):
    """
    Operasyon listesi için context oluşturur.
    
    Args:
        operations: Sayfalandırılmış operasyonlar
        month: Seçili ay
        year: Seçili yıl
        year_list: Yıl listesi
        companies: Müşteri şirketleri
        staffs: Personel listesi
        stats: İstatistikler
        current_filters: Mevcut filtreler
        
    Returns:
        dict: Context
    """
    return {
        'operations': operations,
        'selected_month': month,
        'selected_year': year,
        'year_list': year_list,
        'companies': companies,
        'staffs': staffs,
        **stats,
        'total_count': operations.paginator.count,
        'current_filters': current_filters
    }

def get_job_list_dates():
    """
    İş listesi için tarihleri hesaplar.
    
    Returns:
        tuple: (today, tomorrow, nextday, dates)
    """
    today = timezone.now().date()
    tomorrow = today + timezone.timedelta(days=1)
    nextday = today + timezone.timedelta(days=2)
    dates = [today, tomorrow, nextday]
    return today, tomorrow, nextday, dates

def get_job_list_base_query(dates, company=None, staff=None):
    """
    İş listesi için temel sorguyu oluşturur.
    
    Args:
        dates: Tarih listesi
        company: Şirket (varsa)
        staff: Personel (varsa)
        
    Returns:
        QuerySet: Filtrelenmiş ve optimize edilmiş sorgu
    """
    base_query = (Operationitem.objects
        .filter(
            is_delete=False,
            is_processed=False,
            day__date__in=dates
        )
        .select_related(
            'day',
            'day__operation',
            'day__operation__follow_staff__user',
            'day__operation__selling_staff__user',
            'day__operation__buyer_company',
            'tour',
            'transfer',
            'vehicle',
            'supplier',
            'hotel',
            'activity',
            'activity_supplier',
            'guide'
        )
        .prefetch_related(
            'new_museum',
            'files',
            'day__operation__follow_staff',
            'day__operation__selling_staff'
        )
        .defer(
            'day__operation__follow_staff__dark_mode',
            'day__operation__follow_staff__created_at',
            'day__operation__follow_staff__is_delete',
            'day__operation__selling_staff__dark_mode',
            'day__operation__selling_staff__created_at',
            'day__operation__selling_staff__is_delete',
            'tour__created_at',
            'tour__updated_at',
            'transfer__created_at',
            'transfer__updated_at',
            'hotel__mail',
            'hotel__one_person',
            'hotel__two_person',
            'hotel__tree_person',
            'hotel__finish',
            'hotel__currency',
            'guide__doc_no',
            'guide__phone',
            'guide__mail',
            'guide__price',
            'guide__currency'
        ))
    
    if company:
        base_query = base_query.filter(company=company)
    if staff:
        base_query = base_query.filter(day__operation__follow_staff=staff)
        
    return base_query.order_by('day__date', 'pick_time')

def get_job_list_search_query(start_date, end_date, company=None, staff=None):
    """
    İş listesi için tarih araması sorgusunu oluşturur.
    
    Args:
        start_date: Başlangıç tarihi
        end_date: Bitiş tarihi (varsa)
        company: Şirket (varsa)
        staff: Personel (varsa)
        
    Returns:
        QuerySet: Filtrelenmiş ve optimize edilmiş sorgu
    """
    search_query = (Operationitem.objects
        .filter(is_delete=False)
        .select_related(
            'day',
            'day__operation',
            'day__operation__follow_staff__user',
            'day__operation__selling_staff__user',
            'day__operation__buyer_company',
            'tour',
            'transfer',
            'vehicle',
            'supplier',
            'hotel',
            'activity',
            'activity_supplier',
            'guide'
        )
        .prefetch_related(
            'new_museum',
            'files',
            'day__operation__follow_staff',
            'day__operation__selling_staff'
        )
        .defer(
            'day__operation__follow_staff__dark_mode',
            'day__operation__follow_staff__created_at',
            'day__operation__follow_staff__is_delete',
            'day__operation__selling_staff__dark_mode',
            'day__operation__selling_staff__created_at',
            'day__operation__selling_staff__is_delete',
            'tour__created_at',
            'tour__updated_at',
            'transfer__created_at',
            'transfer__updated_at',
            'hotel__mail',
            'hotel__one_person',
            'hotel__two_person',
            'hotel__tree_person',
            'hotel__finish',
            'hotel__currency',
            'guide__doc_no',
            'guide__phone',
            'guide__mail',
            'guide__price',
            'guide__currency'
        ))
    
    if company:
        search_query = search_query.filter(company=company)
    if staff:
        search_query = search_query.filter(day__operation__follow_staff=staff)
        
    if end_date:
        date_filter = {
            'day__date__gte': start_date,
            'day__date__lte': end_date
        }
    else:
        date_filter = {'day__date': start_date}
        
    return search_query.filter(**date_filter).order_by('day__date', 'pick_time')

def get_job_list_context(today, tomorrow, nextday, items_by_date, search_date=None):
    """
    İş listesi için context oluşturur.
    
    Args:
        today: Bugünün tarihi
        tomorrow: Yarının tarihi
        nextday: Öbür günün tarihi
        items_by_date: Tarihe göre gruplanmış öğeler
        search_date: Tarih araması sonuçları (varsa)
        
    Returns:
        dict: Context
    """
    return {
        'today': today,
        'tomorrow': tomorrow,
        'nextday': nextday,
        'today_items': items_by_date[today],
        'tomorrow_items': items_by_date[tomorrow],
        'nextday_items': items_by_date[nextday],
        'search_date': search_date,
        'job': True
    }

def create_job_list_log(request, company=None, staff=None, is_search=False, start_date=None, end_date=None):
    """
    İş listesi için log kaydı oluşturur.
    
    Args:
        request: Django HTTP request
        company: Şirket (varsa)
        staff: Personel (varsa)
        is_search: Tarih araması mı?
        start_date: Başlangıç tarihi (varsa)
        end_date: Bitiş tarihi (varsa)
    """
    log_data = {
        'ip_address': get_client_ip(request),
        'browser_info': request.META.get('HTTP_USER_AGENT', '')
    }
    
    if is_search and staff:
        log_data.update({
            'company': company,
            'staff': staff,
            'action': f"İş listesinde tarih araması yaptı: {start_date} - {end_date or start_date}"
        })
    elif staff:
        log_data.update({
            'company': company,
            'staff': staff,
            'action': "Günlük iş listesini görüntüledi"
        })
    else:
        log_data.update({
            'action': "Süper kullanıcı günlük iş listesini görüntüledi"
        })
        
    UserActivityLog.objects.create(**log_data) 

def save_operation_file_form(form, operation, operation_item=None):
    """
    Operasyon dosyası formunu kaydeder.
    
    Args:
        form: OperationFileForm instance'ı
        operation: Operation modeli instance'ı
        operation_item: Operationitem modeli instance'ı (varsa)
        
    Returns:
        tuple: (success, file, error_message)
    """
    try:
        if form.is_valid():
            file = form.save(commit=False)
            file.operation = operation
            if operation_item:
                file.operation_item = operation_item
            file.save()
            return True, file, None
        return False, None, form.errors
    except Exception as e:
        logger.error(f"Operasyon dosyası kaydetme hatası: {str(e)}")
        return False, None, str(e)

def get_operation_file_context(form, operation, operation_item=None):
    """
    Operasyon dosyası için context oluşturur.
    
    Args:
        form: OperationFileForm instance'ı
        operation: Operation modeli instance'ı
        operation_item: Operationitem modeli instance'ı (varsa)
        
    Returns:
        dict: Context
    """
    context = {
        'form': form,
        'operation': operation
    }
    
    if operation_item:
        context['item'] = operation_item
        
    return context

def get_operation_file_template(operation_item=None):
    """
    Operasyon dosyası için template adını döndürür.
    
    Args:
        operation_item: Operationitem modeli instance'ı (varsa)
        
    Returns:
        str: Template adı
    """
    return 'operation/operationitemfile_form.html' if operation_item else 'operation/operationfile_form.html'

def get_operation_file_partial_template(operation_item=None):
    """
    Operasyon dosyası için partial template adını döndürür.
    
    Args:
        operation_item: Operationitem modeli instance'ı (varsa)
        
    Returns:
        str: Partial template adı
    """
    return 'operation/partials/item-table.html' if operation_item else 'operation/partials/operation-card.html'

def get_operation_file_context_data(operation_item=None):
    """
    Operasyon dosyası için partial template context'ini döndürür.
    
    Args:
        operation_item: Operationitem modeli instance'ı (varsa)
        
    Returns:
        dict: Context
    """
    return {'item': operation_item} if operation_item else {'operation': operation_item.day.operation} 

def get_cost_for_item(item):
    """
    Operasyon öğesi için maliyet bilgisini getirir.
    
    Args:
        item: Operationitem modeli instance'ı
        
    Returns:
        Cost: Maliyet nesnesi veya None
    """
    try:
        if item.operation_type == "Transfer" and item.transfer:
            return Cost.objects.get(
                transfer=item.transfer,
                supplier=item.supplier,
                is_delete=False,
                company=item.company
            )
        elif item.operation_type in ["Tur", "TurTransfer", "TransferTur"] and item.tour:
            return Cost.objects.get(
                tour=item.tour,
                supplier=item.supplier,
                is_delete=False,
                company=item.company
            )
    except Cost.DoesNotExist:
        logger.warning(f"Maliyet bulunamadı: {item}")
    return None

def calculate_vehicle_cost(item, cost):
    """
    Araç maliyetini hesaplar.
    
    Args:
        item: Operationitem modeli instance'ı
        cost: Cost modeli instance'ı
        
    Returns:
        float: Hesaplanan maliyet
    """
    if not cost or not item.vehicle:
        return 0
        
    vehicle_cost_map = {
        "BINEK": cost.car,
        "MINIVAN": cost.minivan,
        "MINIBUS": cost.minibus,
        "MIDIBUS": cost.midibus,
        "OTOBUS": cost.bus
    }
    
    return vehicle_cost_map.get(item.vehicle.vehicle, 0)

def update_item_costs(items, days_back=1, include_activity=True):
    """
    Operasyon öğelerinin maliyetlerini günceller.
    
    Args:
        items: Operationitem queryset'i
        days_back: Kaç gün öncesinden itibaren güncelleneceği
        include_activity: Aktivite maliyetlerinin de güncellenip güncellenmeyeceği
    """
    from datetime import date, timedelta
    
    start_date = date.today() - timedelta(days=days_back)
    items = items.filter(day__date__gte=start_date)
    
    if not include_activity:
        items = items.filter(activity__isnull=True)
    
    for item in items:
        # Manuel fiyat varsa onu kullan
        if item.manuel_vehicle_price:
            item.vehicle_price = item.manuel_vehicle_price
        # Araç ve tedarikçi varsa maliyet hesapla
        elif not item.vehicle_price and item.vehicle and item.supplier:
            cost = get_cost_for_item(item)
            if cost:
                item.vehicle_price = calculate_vehicle_cost(item, cost)
        
        # Aktivite maliyeti güncelleme
        if include_activity and item.activity and item.manuel_activity_price:
            item.activity_price = item.manuel_activity_price
            
        item.save() 

def toggle_operation(operation):
    """
    Operasyonu ve ilişkili tüm öğeleri siler/geri yükler.
    Performans için bulk_update kullanır.
    
    Args:
        operation: Operation modeli instance'ı
        
    Returns:
        tuple: (success, error_message, is_deleted)
    """
    try:
        # İlişkili tüm öğeleri tek sorguda getir ve prefetch_related ile optimize et
        operation = Operation.objects.prefetch_related(
            'days',
            'days__items'
        ).get(pk=operation.pk)
        
        days = list(operation.days.all())
        items = []
        for day in days:
            items.extend(list(day.items.all()))
        
        # Yeni durumu belirle
        new_status = not operation.is_delete
        
        # Tüm öğeleri yeni duruma göre işaretle
        for day in days:
            day.is_delete = new_status
        for item in items:
            item.is_delete = new_status
            
        # Bulk update ile toplu güncelleme yap
        if days:
            Operationday.objects.bulk_update(days, ['is_delete'])
        if items:
            Operationitem.objects.bulk_update(items, ['is_delete'])
        
        # Operasyonu yeni duruma göre işaretle
        operation.is_delete = new_status
        if operation.is_delete:
            operation.ticket = f"{operation.ticket}Silindi"
        else:
            operation.ticket = operation.ticket.replace("Silindi", "")
        operation.save(update_fields=['is_delete', 'ticket'])
        
        return True, None, new_status
        
    except Exception as e:
        logger.error(f"Operasyon {'geri yükleme' if operation.is_delete else 'silme'} hatası: {str(e)}")
        return False, str(e), operation.is_delete

def toggle_operation_item(item):
    """
    Operasyon öğesini siler/geri yükler.
    Performans için update_fields kullanır.
    
    Args:
        item: Operationitem modeli instance'ı
        
    Returns:
        tuple: (success, error_message, is_deleted)
    """
    try:
        # Öğeyi yeni duruma göre işaretle
        new_status = not item.is_delete
        item.is_delete = new_status
        item.save(update_fields=['is_delete'])
        
        return True, None, new_status
        
    except Exception as e:
        logger.error(f"Operasyon öğesi {'geri yükleme' if item.is_delete else 'silme'} hatası: {str(e)}")
        return False, str(e), item.is_delete

def get_operation_toggle_log_message(operation, is_deleted, is_superuser=False):
    """
    Operasyon silme/geri yükleme log mesajını oluşturur.
    
    Args:
        operation: Operation modeli instance'ı
        is_deleted: Silme mi geri yükleme mi?
        is_superuser: Süper kullanıcı mı?
        
    Returns:
        str: Log mesajı
    """
    prefix = "Süper kullanıcı " if is_superuser else ""
    action = "geri yükledi" if is_deleted else "sildi"
    return f"{prefix}Operasyonu {action}: {operation.ticket} (#{operation.buyer_company.name})"

def get_operation_item_toggle_log_message(item, is_deleted, is_superuser=False):
    """
    Operasyon öğesi silme/geri yükleme log mesajını oluşturur.
    
    Args:
        item: Operationitem modeli instance'ı
        is_deleted: Silme mi geri yükleme mi?
        is_superuser: Süper kullanıcı mı?
        
    Returns:
        str: Log mesajı
    """
    prefix = "Süper kullanıcı " if is_superuser else ""
    action = "geri yükledi" if is_deleted else "sildi"
    return f"{prefix}Operasyon öğesini {action}: {item.operation_type} ({item.day.date})"

def toggle_operation_day(day):
    """
    Operasyon gününü ve ilişkili öğeleri siler/geri yükler.
    Performans için bulk_update kullanır.
    
    Args:
        day: Operationday modeli instance'ı
        
    Returns:
        tuple: (success, error_message, is_deleted)
    """
    try:
        # İlişkili tüm öğeleri tek sorguda getir
        items = list(day.items.all())
        
        # Yeni durumu belirle
        new_status = not day.is_delete
        
        # Tüm öğeleri yeni duruma göre işaretle
        for item in items:
            item.is_delete = new_status
            
        # Bulk update ile toplu güncelleme yap
        if items:
            Operationitem.objects.bulk_update(items, ['is_delete'])
        
        # Günü yeni duruma göre işaretle
        day.is_delete = new_status
        day.save(update_fields=['is_delete'])
        
        return True, None, new_status
        
    except Exception as e:
        logger.error(f"Operasyon günü {'geri yükleme' if day.is_delete else 'silme'} hatası: {str(e)}")
        return False, str(e), day.is_delete

def get_operation_day_toggle_log_message(day, is_deleted, is_superuser=False):
    """
    Operasyon günü silme/geri yükleme log mesajını oluşturur.
    
    Args:
        day: Operationday modeli instance'ı
        is_deleted: Silme mi geri yükleme mi?
        is_superuser: Süper kullanıcı mı?
        
    Returns:
        str: Log mesajı
    """
    prefix = "Süper kullanıcı " if is_superuser else ""
    action = "geri yükledi" if is_deleted else "sildi"
    return f"{prefix}Operasyon gününü {action}: {day.date} ({day.operation.ticket})"

def get_deleted_items_query(company=None, staff=None):
    """
    Silinmiş operasyon öğeleri için temel sorguyu oluşturur.
    
    Args:
        company: Şirket (varsa)
        staff: Personel (varsa)
        
    Returns:
        QuerySet: Filtrelenmiş ve optimize edilmiş sorgu
    """
    base_query = Operationitem.objects.select_related(
        'day',
        'day__operation',
        'day__operation__buyer_company',
        'tour',
        'transfer',
        'vehicle',
        'supplier',
        'hotel',
        'activity',
        'activity_supplier',
        'guide'
    ).filter(is_delete=True)
    
    if company:
        base_query = base_query.filter(company=company)
    if staff:
        base_query = base_query.filter(day__operation__follow_staff=staff)
        
    return base_query.order_by('-day__date', '-pick_time')

def apply_item_filters(query, search_params):
    """
    Operasyon öğelerine filtreleri uygular.
    
    Args:
        query: Temel sorgu
        search_params: Arama parametreleri
        
    Returns:
        QuerySet: Filtrelenmiş sorgu
    """
    if search_params.get('query'):
        query = query.filter(
            Q(operation_type__icontains=search_params['query']) |
            Q(driver__icontains=search_params['query']) |
            Q(plaka__icontains=search_params['query']) |
            Q(pick_location__icontains=search_params['query']) |
            Q(drop_location__icontains=search_params['query'])
        )
        
    if search_params.get('start_date'):
        if search_params.get('end_date'):
            query = query.filter(
                day__date__gte=search_params['start_date'],
                day__date__lte=search_params['end_date']
            )
        else:
            query = query.filter(day__date=search_params['start_date'])
            
    return query 