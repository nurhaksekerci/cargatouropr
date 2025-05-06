from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


CITY_CHOICES = (
    ('Adana', 'Adana'),
    ('Adıyaman', 'Adıyaman'),
    ('Afyonkarahisar', 'Afyonkarahisar'),
    ('Ağrı', 'Ağrı'),
    ('Aksaray', 'Aksaray'),
    ('Amasya', 'Amasya'),
    ('Ankara', 'Ankara'),
    ('Antalya', 'Antalya'),
    ('Ardahan', 'Ardahan'),
    ('Artvin', 'Artvin'),
    ('Aydın', 'Aydın'),
    ('Balıkesir', 'Balıkesir'),
    ('Bartın', 'Bartın'),
    ('Batman', 'Batman'),
    ('Bayburt', 'Bayburt'),
    ('Bilecik', 'Bilecik'),
    ('Bingöl', 'Bingöl'),
    ('Bitlis', 'Bitlis'),
    ('Bolu', 'Bolu'),
    ('Burdur', 'Burdur'),
    ('Bursa', 'Bursa'),
    ('Çanakkale', 'Çanakkale'),
    ('Çankırı', 'Çankırı'),
    ('Çorum', 'Çorum'),
    ('Denizli', 'Denizli'),
    ('Diyarbakır', 'Diyarbakır'),
    ('Düzce', 'Düzce'),
    ('Edirne', 'Edirne'),
    ('Elazığ', 'Elazığ'),
    ('Erzincan', 'Erzincan'),
    ('Erzurum', 'Erzurum'),
    ('Eskişehir', 'Eskişehir'),
    ('Gaziantep', 'Gaziantep'),
    ('Giresun', 'Giresun'),
    ('Gümüşhane', 'Gümüşhane'),
    ('Hakkari', 'Hakkari'),
    ('Hatay', 'Hatay'),
    ('Iğdır', 'Iğdır'),
    ('Isparta', 'Isparta'),
    ('İstanbul', 'İstanbul'),
    ('İstanbul (Avrupa)', 'İstanbul (Avrupa)'),
    ('İstanbul (Anadolu)', 'İstanbul (Anadolu)'),
    ('İzmir', 'İzmir'),
    ('Kahramanmaraş', 'Kahramanmaraş'),
    ('Karabük', 'Karabük'),
    ('Karaman', 'Karaman'),
    ('Kars', 'Kars'),
    ('Kastamonu', 'Kastamonu'),
    ('Kayseri', 'Kayseri'),
    ('Kırıkkale', 'Kırıkkale'),
    ('Kırklareli', 'Kırklareli'),
    ('Kırşehir', 'Kırşehir'),
    ('Kilis', 'Kilis'),
    ('Kocaeli', 'Kocaeli'),
    ('Konya', 'Konya'),
    ('Kütahya', 'Kütahya'),
    ('Malatya', 'Malatya'),
    ('Manisa', 'Manisa'),
    ('Mardin', 'Mardin'),
    ('Mersin', 'Mersin'),
    ('Muğla', 'Muğla'),
    ('Muş', 'Muş'),
    ('Nevşehir', 'Nevşehir'),
    ('Niğde', 'Niğde'),
    ('Ordu', 'Ordu'),
    ('Osmaniye', 'Osmaniye'),
    ('Rize', 'Rize'),
    ('Sakarya', 'Sakarya'),
    ('Samsun', 'Samsun'),
    ('Siirt', 'Siirt'),
    ('Sinop', 'Sinop'),
    ('Sivas', 'Sivas'),
    ('Şanlıurfa', 'Şanlıurfa'),
    ('Şırnak', 'Şırnak'),
    ('Tekirdağ', 'Tekirdağ'),
    ('Tokat', 'Tokat'),
    ('Trabzon', 'Trabzon'),
    ('Tunceli', 'Tunceli'),
    ('Uşak', 'Uşak'),
    ('Van', 'Van'),
    ('Yalova', 'Yalova'),
    ('Yozgat', 'Yozgat'),
    ('Zonguldak', 'Zonguldak'),
    ('Türkiye', 'Türkiye'),
    ('Marmara', 'Marmara'),
    ('Ege', 'Ege'),
    ('Akdeniz', 'Akdeniz'),
    ('İç Anadolu', 'İç Anadolu'),
    ('Doğu Anadolu', 'Doğu Anadolu'),
    ('Güneydoğu Anadolu', 'Güneydoğu Anadolu'),
    ('Karadeniz', 'Karadeniz'),
)

CURRENCY_CHOICES = (
    ('TL', 'TL'),
    ('USD', 'USD'),
    ('EUR', 'EUR'),
    ('RMB', 'RMB'),
)

TRUE_FALSE_CHOICES = (
    ('Yes', 'Yes'),
    ('No', 'No'),
)

class Sirket(models.Model):
    STATU_CHOICES = (
        ('demo', 'Demo'),
        ('basic', 'Basic'),
        ('team', 'Team'),
        ('professional', 'Professional'),
    )
    name = models.CharField(verbose_name="Adı", max_length=155, db_index=True)
    start = models.DateField(verbose_name="Başlama Tarihi")
    finish = models.DateField(verbose_name="Bitiş Tarihi")
    is_active = models.BooleanField(verbose_name="Aktif mi?", db_index=True)
    logo = models.ImageField(verbose_name="Logo", upload_to='company_logos/', null=True, blank=True)
    statu = models.CharField(max_length=20, choices=STATU_CHOICES, verbose_name="Statü", default="demo", db_index=True)
    created_at = models.DateField(verbose_name="Kurulma Tarihi", auto_now_add=True, blank=True, null=True)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)
    slug = models.SlugField(verbose_name="Slug", unique=True, blank=True, null=True)
    updated_at = models.DateField(verbose_name="Güncelleme Tarihi", auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Şirket"
        verbose_name_plural = "Şirketler"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super(Sirket, self).save(*args, **kwargs)

    def generate_unique_slug(self):
        original_slug = slugify(self.name.replace('ı', 'i').replace('İ', 'I'))
        slug = original_slug
        counter = 1
        while Sirket.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        return slug

class Personel(models.Model):
    JOB_CHOICES = (
        ('Satış Personeli', 'Satış Personeli'),
        ('Operasyon Şefi', 'Operasyon Şefi'),
        ('Yönetim', 'Yönetim'),
        ('Muhasebe', 'Muhasebe'),
        ('Sistem Geliştiricisi', 'Sistem Geliştiricisi'),
    )
    GENDER_CHOICES = (
        ('man', 'Man'),
        ('woman', 'Woman'),
    )
    user = models.ForeignKey(User, verbose_name="User", on_delete=models.CASCADE, related_name='personel')
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="personeller")
    is_active = models.BooleanField(verbose_name="Aktif mi?", default=True, db_index=True)
    phone = models.CharField(verbose_name="Telefon", max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="man", verbose_name="Cinsiyet")
    job = models.CharField(max_length=20, choices=JOB_CHOICES, verbose_name="Görevi", default="Satış Personeli", db_index=True)
    created_at = models.DateField(verbose_name="Kurulma Tarihi", auto_now_add=True, blank=True, null=True)
    dark_mode = models.BooleanField(verbose_name="Dark Mode", default=False)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Personel"
        verbose_name_plural = "Personeller"

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name.upper()

class Tour(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="turlar")
    route = models.CharField(verbose_name="Güzergah", max_length=155, db_index=True)
    start_city = models.CharField(verbose_name="Başlangıç Şehri", max_length=155, choices=CITY_CHOICES, blank=True, null=True, db_index=True)
    finish_city = models.CharField(verbose_name="Bitiş Şehri", max_length=155, choices=CITY_CHOICES, blank=True, null=True)
    created_at = models.DateField(verbose_name="Kurulma Tarihi", auto_now_add=True, blank=True, null=True)
    updated_at = models.DateField(verbose_name="Güncelleme Tarihi", auto_now=True)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Tur"
        verbose_name_plural = "Turlar"

    def __str__(self):
        return self.route

class Transfer(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="transferler")
    route = models.CharField(verbose_name="Güzergah", max_length=155, db_index=True)
    start_city = models.CharField(verbose_name="Başlangıç Şehri", max_length=155, choices=CITY_CHOICES, blank=True, null=True, db_index=True)
    finish_city = models.CharField(verbose_name="Bitiş Şehri", max_length=155, choices=CITY_CHOICES, blank=True, null=True)
    created_at = models.DateField(verbose_name="Kurulma Tarihi", auto_now_add=True, blank=True, null=True)
    updated_at = models.DateField(verbose_name="Güncelleme Tarihi", auto_now=True)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Transfer"
        verbose_name_plural = "Transferler"

    def __str__(self):
        return self.route

class Vehicle(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="araçlar")
    vehicle = models.CharField(verbose_name="Araç", max_length=155, db_index=True)
    capacity = models.PositiveIntegerField(verbose_name="Kapasite")
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Araç"
        verbose_name_plural = "Araçlar"

    def __str__(self):
        return self.vehicle

class Guide(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="rehberler")
    name = models.CharField(verbose_name="Adı", max_length=155, db_index=True)
    city = models.CharField(verbose_name="Şehir", max_length=155, choices=CITY_CHOICES, blank=True, null=True, db_index=True)
    doc_no = models.CharField(verbose_name="Rehber No", max_length=155, blank=True, null=True)
    phone = models.CharField(verbose_name="Telefon No", max_length=155)
    mail = models.CharField(verbose_name="Mail", max_length=155, blank=True, null=True)
    price = models.DecimalField(verbose_name="Ücreti", max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Para Birimi", default="TL")
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Rehber"
        verbose_name_plural = "Rehberler"

    def __str__(self):
        return f"{self.city} - {self.name}"

class Hotel(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="oteller")
    name = models.CharField(verbose_name="Adı", max_length=100, db_index=True)
    city = models.CharField(verbose_name="Şehir", max_length=155, choices=CITY_CHOICES, blank=True, null=True, db_index=True)
    mail = models.CharField(verbose_name="Mail", max_length=155, blank=True, null=True)
    one_person = models.DecimalField(verbose_name="Tek Kişilik Ücreti", max_digits=10, decimal_places=2, default=0)
    two_person = models.DecimalField(verbose_name="İki Kişilik Ücreti", max_digits=10, decimal_places=2, default=0)
    tree_person = models.DecimalField(verbose_name="Üç Kişilik Ücreti", max_digits=10, decimal_places=2, default=0)
    finish = models.DateField(verbose_name="Fiyat Geçerlilik Tarihi", blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Para Birimi", default="TL")
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Otel"
        verbose_name_plural = "Oteller"

    def __str__(self):
        return f"{self.name} - {self.city}"

class Activity(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="aktiviteler")
    name = models.CharField(verbose_name="Adı", max_length=100, db_index=True)
    city = models.CharField(verbose_name="Şehir", max_length=155, choices=CITY_CHOICES, blank=True, null=True, db_index=True)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Aktivite"
        verbose_name_plural = "Aktiviteler"

    def __str__(self):
        return f"{self.city} - {self.name}"

class Museum(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="müzeler")
    name = models.CharField(verbose_name="Adı", max_length=100, db_index=True)
    city = models.CharField(verbose_name="Şehir", max_length=155, choices=CITY_CHOICES, blank=True, null=True, db_index=True)
    contact = models.CharField(verbose_name="İletişim", max_length=155, blank=True, null=True)
    price = models.DecimalField(verbose_name="Ücreti", max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Para Birimi", default="TL")
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Müze"
        verbose_name_plural = "Müzeler"

    def __str__(self):
        return f"{self.city} - {self.name}"

class Supplier(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="tedarikçiler")
    name = models.CharField(verbose_name="Adı", max_length=100, db_index=True)
    contact = models.CharField(verbose_name="İletişim", max_length=155)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Tedarikçi"
        verbose_name_plural = "Tedarikçiler"

    def __str__(self):
        return f"{self.name}"

class Activitysupplier(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="aktivite_tedarikçileri")
    name = models.CharField(verbose_name="Adı", max_length=100, db_index=True)
    contact = models.CharField(verbose_name="İletişim", max_length=155)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Aktivite Tedarikçisi"
        verbose_name_plural = "Aktivite Tedarikçileri"

    def __str__(self):
        return f"{self.name}"

class Cost(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="maliyetler")
    supplier = models.ForeignKey(Supplier, verbose_name="Tedarikçi", on_delete=models.SET_NULL, blank=True, null=True, related_name="maliyetler")
    tour = models.ForeignKey(Tour, verbose_name="Tur", on_delete=models.SET_NULL, blank=True, null=True, related_name="maliyetler")
    transfer = models.ForeignKey(Transfer, verbose_name="Transfer", on_delete=models.SET_NULL, blank=True, null=True, related_name="maliyetler")
    car = models.DecimalField(verbose_name="Maliyet Binek", max_digits=10, decimal_places=2, blank=True, null=True)
    minivan = models.DecimalField(verbose_name="Maliyet Minivan", max_digits=10, decimal_places=2, blank=True, null=True)
    minibus = models.DecimalField(verbose_name="Maliyet Minibüs", max_digits=10, decimal_places=2, blank=True, null=True)
    midibus = models.DecimalField(verbose_name="Maliyet Midibüs", max_digits=10, decimal_places=2, blank=True, null=True)
    bus = models.DecimalField(verbose_name="Maliyet Otobüs", max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Para Birimi", default="TL")
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Maliyet"
        verbose_name_plural = "Maliyetler"

    def __str__(self):
        if self.tour != None:
            return f"{self.tour} {self.supplier}"
        else:
            return f"{self.transfer} {self.supplier}"

class Activitycost(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="aktivite_maliyetleri")
    supplier = models.ForeignKey(Activitysupplier, verbose_name="Aktivite Tedarikçisi", on_delete=models.SET_NULL, blank=True, null=True, related_name="aktivite_maliyetleri")
    activity = models.ForeignKey(Activity, verbose_name="Activite", on_delete=models.SET_NULL, blank=True, null=True, related_name="maliyetler")
    price = models.DecimalField(verbose_name="Ücreti", max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Para Birimi", default="TL")
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Aktivite Maliyeti"
        verbose_name_plural = "Aktivite Maliyetleri"

    def __str__(self):
        return f"{self.supplier} - {self.activity}"

class Buyercompany(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, blank=True, null=True, related_name="alıcı_firmalar")
    name = models.CharField(verbose_name="Adı", max_length=100, db_index=True)
    short_name = models.CharField(verbose_name="Kısa adı", max_length=5, unique=True, db_index=True)
    contact = models.CharField(verbose_name="İletişim", max_length=155, blank=True, null=True)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Alıcı Firma"
        verbose_name_plural = "Alıcı Firmalar"

    def __str__(self):
        return self.name

class UserActivityLog(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, blank=True, null=True, related_name="kullanıcı_logları")
    staff = models.ForeignKey(Personel, verbose_name="Personel", on_delete=models.SET_NULL, blank=True, null=True, related_name="aktivite_logları")
    action = models.TextField(verbose_name="İşlem")
    ip_address = models.GenericIPAddressField(verbose_name="IP Adresi", blank=True, null=True)
    browser_info = models.TextField(verbose_name="Tarayıcı Bilgisi", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Kullanıcı İşlem Logu"
        verbose_name_plural = "Kullanıcı İşlem Logları"

    def __str__(self):
        return f"{self.staff} - {self.action} - {self.timestamp}"

class Operation(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('Pesin', 'Peşin'),
        ('Taksitli', 'Taksitli'),
        ('Parcalı', 'Parçalı'),
    )
    PAYMENT_CHANNEL_CHOICES = (
        ('Havale', 'Havale'),
        ('Xctrip', 'Xctrip'),
    )
    SOLD_CHOICES = (
        ('Istendi', 'Istendi'),
        ('Alındı', 'Alındı'),
    )
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="operasyonlar")
    selling_staff = models.ForeignKey(Personel, verbose_name="Satan Personel", related_name="sattığı_operasyonlar", on_delete=models.SET_NULL, blank=True, null=True)
    follow_staff = models.ForeignKey(Personel, verbose_name="Takip Eden Personel", related_name="takip_ettiği_operasyonlar", on_delete=models.SET_NULL, blank=True, null=True)
    create_date = models.DateTimeField(verbose_name="Oluşturulma Tarihi", auto_now=False, auto_now_add=True)
    update_date = models.DateTimeField(verbose_name="Güncelleme Tarihi", auto_now=True, auto_now_add=False)

    buyer_company = models.ForeignKey(Buyercompany, verbose_name="Alıcı Firma", related_name="operasyonlar", on_delete=models.SET_NULL, blank=True, null=True)
    ticket = models.CharField(verbose_name="Tur Etiketi", unique=True, max_length=50, blank=True, null=True, db_index=True)

    start = models.DateField(verbose_name="Başlama Tarihi", db_index=True)
    finish = models.DateField(verbose_name="Bitiş Tarihi")

    passenger_info = models.TextField(verbose_name="Yolcu Bilgileri")
    number_passengers = models.PositiveIntegerField(verbose_name="Yolcu Sayısı", default=1)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, blank=True, null=True, verbose_name="Ödeme Türü", default=None)
    payment_channel = models.CharField(max_length=20, choices=PAYMENT_CHANNEL_CHOICES, blank=True, null=True, verbose_name="Ödeme Kanalı", default=None)
    remaining_payment = models.DecimalField(verbose_name="Kalan Ödeme", max_digits=10, decimal_places=2, default=0)

    tl_sales_price = models.DecimalField(verbose_name="TL Satış Fiyatı", max_digits=10, decimal_places=2, default=0)
    usd_sales_price = models.DecimalField(verbose_name="USD Satış Fiyatı", max_digits=10, decimal_places=2, default=0)
    eur_sales_price = models.DecimalField(verbose_name="EUR Satış Fiyatı", max_digits=10, decimal_places=2, default=0)
    rbm_sales_price = models.DecimalField(verbose_name="RBM Satış Fiyatı", max_digits=10, decimal_places=2, default=0)

    total_sales_price = models.DecimalField(verbose_name="Toplam Satış Fiyatı", max_digits=10, decimal_places=2, default=0)

    tl_cost_price = models.DecimalField(verbose_name="TL Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)
    usd_cost_price = models.DecimalField(verbose_name="USD Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)
    eur_cost_price = models.DecimalField(verbose_name="EUR Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)
    rbm_cost_price = models.DecimalField(verbose_name="RBM Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)

    total_cost_price = models.DecimalField(verbose_name="Toplam Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)

    sold = models.CharField(max_length=20, choices=SOLD_CHOICES, blank=True, null=True, verbose_name='Ödeme Durumu', db_index=True)


    tl_activity_price = models.DecimalField(verbose_name="TL Aktivite Fiyatı", max_digits=10, decimal_places=2, default=0)
    usd_activity_price = models.DecimalField(verbose_name="USD Aktivite Fiyatı", max_digits=10, decimal_places=2, default=0)
    eur_activity_price = models.DecimalField(verbose_name="EUR Aktivite Fiyatı", max_digits=10, decimal_places=2, default=0)
    rbm_activity_price = models.DecimalField(verbose_name="RBM Aktivite Fiyatı", max_digits=10, decimal_places=2, default=0)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Operasyon"
        verbose_name_plural = "Operasyonlar"

    def __str__(self):
        return f"{self.ticket}"

    def save(self, *args, **kwargs):
        if not self.ticket:
            # Ticket boşsa yeni bir değer atama işlemi
            if not self.pk or self.buyer_company.short_name != Operation.objects.get(pk=self.pk).buyer_company.short_name or self.start != Operation.objects.get(pk=self.pk).start:
                kisa_ad = self.buyer_company.short_name
                tarih_format = self.start.strftime("%d%m%y")

                # Benzersiz bir etiket oluşturana kadar döngü
                tur_sayisi = 1
                while True:
                    potansiyel_etiket = f"{kisa_ad}{tarih_format}{str(tur_sayisi).zfill(3)}"
                    if not Operation.objects.filter(ticket=potansiyel_etiket).exclude(pk=self.pk).exists():
                        self.ticket = potansiyel_etiket
                        break
                    tur_sayisi += 1
        else:
            # Ticket zaten varsa, kontrol etmeden kaydet
            pass
        super().save(*args, **kwargs)

class Operationday(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="operasyon_günleri")
    operation = models.ForeignKey(Operation, verbose_name="Operasyon", on_delete=models.CASCADE, related_name="days")
    date = models.DateField(verbose_name="Tarih", db_index=True)
    day_number = models.PositiveIntegerField(verbose_name="Gün Numarası", default=1)
    create_date = models.DateTimeField(verbose_name="Oluşturulma Tarihi", auto_now=False, auto_now_add=True, blank=True, null=True)
    update_date = models.DateTimeField(verbose_name="Güncelleme Tarihi", auto_now=True, auto_now_add=False, blank=True, null=True)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Operasyon Günü"
        verbose_name_plural = "Operasyon Günleri"
        ordering = ['date']

    def __str__(self):
        return f"{self.date.strftime('%d-%m-%Y')} - {self.operation.ticket}"

class Operationitem(models.Model):
    OPERATIONSTYPE_CHOICES = (
        ('Transfer', 'Transfer'),
        ('Tur', 'Tur'),
        ('TurTransfer', 'Tur + Transfer'),
        ('TransferTur', 'Transfer + Tur'),
        ('Arac', 'Araç'),
        ('Aktivite', 'Aktivite'),
        ('Muze', 'Müze'),
        ('Otel', 'Otel'),
        ('Rehber', 'Rehber'),
        ('Aracli Rehber', 'Araçlı Rehber'),
        ('Serbest Zaman', 'Serbest Zaman'),
    )
    ROOMTYPE_CHOICES = (
        ('Tek', 'Tek'),
        ('Cift', 'Çift'),
        ('Uc', 'Üç'),
    )

    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="operasyon_öğeleri")
    day = models.ForeignKey(Operationday, verbose_name="Gün", on_delete=models.CASCADE, related_name="items")

    operation_type = models.CharField(max_length=20, choices=OPERATIONSTYPE_CHOICES, verbose_name="İşlem Türü", db_index=True)
    pick_time = models.TimeField(blank=True, null=True, verbose_name="Alış Saati")
    release_time = models.TimeField(blank=True, null=True, verbose_name="Bırakış Saati")
    release_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Bırakış Yeri")
    pick_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alış Yeri")


    tour = models.ForeignKey(Tour, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Tur", related_name="operasyon_öğeleri")
    transfer = models.ForeignKey(Transfer, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Transfer", related_name="operasyon_öğeleri")
    vehicle = models.ForeignKey(Vehicle, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Araç", related_name="operasyon_öğeleri")
    supplier = models.ForeignKey(Supplier, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Araç Tedarikçi", related_name="operasyon_öğeleri")
    manuel_vehicle_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Manuel Araç Ücreti")
    auto_vehicle_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Hesaplanan Araç Ücreti")
    vehicle_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Araç Ücreti", blank=True, null=True)
    vehicle_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Araç Satış Ücreti")
    vehicle_sell_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Araç Satış Birimi", default="TL")
    vehicle_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Araç Para Birimi", default="TL")
    cost = models.ForeignKey(Cost, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Araç Maaliyet", related_name="operasyon_öğeleri")

    hotel = models.ForeignKey(Hotel, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Otel", related_name="operasyon_öğeleri")
    room_type = models.CharField(max_length=20, choices=ROOMTYPE_CHOICES, blank=True, null=True, verbose_name="Oda Türü")
    hotel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Otel Ücreti")
    hotel_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Otel Satış Ücreti")
    hotel_sell_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Otel Satış Birimi", default="USD")
    hotel_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Otel Para Birimi", default="USD")
    hotel_payment = models.CharField(max_length=20, choices=TRUE_FALSE_CHOICES, verbose_name="Otel Ödemesi Bizde", default="No")

    activity = models.ForeignKey(Activity, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Aktivite", related_name="operasyon_öğeleri")
    activity_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Kayıtlı Aktivite Ücreti")
    activity_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Aktivite Satış Ücreti")
    manuel_activity_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Manuel Aktivite Ücreti")
    auto_activity_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Hesaplanan Aktivite Ücreti")
    activity_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Aktivite Para Birimi", default="USD")
    activity_sell_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Aktivite Satış Birimi", default="USD")
    activity_supplier = models.ForeignKey(Activitysupplier, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Aktivite Tedarikçi", related_name="operasyon_öğeleri")
    activity_cost = models.ForeignKey(Activitycost, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Aktivite Maliyet", related_name="operasyon_öğeleri")
    activity_payment = models.CharField(max_length=20, choices=TRUE_FALSE_CHOICES, verbose_name="Activite Ödemesi Bizde", default="No")

    new_museum = models.ManyToManyField(Museum, blank=True, verbose_name="Müzeler", related_name="operasyon_öğeleri")
    museum_person = models.IntegerField(verbose_name="Kişi Sayısı", default=0)
    museum_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Müze Ücreti")
    museum_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Müze Satış Ücreti")
    museum_sell_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Müze Satış Birimi", default="USD")
    museum_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Müze Para Birimi", default="USD")
    museum_payment = models.CharField(max_length=20, choices=TRUE_FALSE_CHOICES, verbose_name="Müze Ödemesi Bizde", default="No")

    driver = models.CharField(max_length=255, blank=True, null=True, verbose_name="Şoför")
    driver_phone = models.CharField(max_length=255, blank=True, null=True, verbose_name="Şoför Telefon")
    plaka = models.CharField(max_length=255, blank=True, null=True, verbose_name="Plaka")
    guide = models.ForeignKey(Guide, blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Rehber", related_name="operasyon_öğeleri")
    guide_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Rehber Ücreti")
    guide_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Rehber Satış Ücreti")
    guide_sell_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Rehber Satış Birimi", default="USD")
    guide_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Rehber Para Birimi", default="USD")
    guide_var = models.CharField(max_length=20, choices=TRUE_FALSE_CHOICES, verbose_name="Rehber var mı?", default="No")
    other_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Diğer")
    other_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Diğer Para Birimi", default="USD")
    other_sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Diğer Satış")
    other_sell_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Diğer Satış Birimi", default="USD")


    tl_cost_price = models.DecimalField(verbose_name="TL Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)
    usd_cost_price = models.DecimalField(verbose_name="USD Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)
    eur_cost_price = models.DecimalField(verbose_name="EUR Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)
    rmb_cost_price = models.DecimalField(verbose_name="RMB Maliyet Fiyatı", max_digits=10, decimal_places=2, default=0)

    description = models.TextField(verbose_name="Tur Detayı", blank=True, null=True)

    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)
    is_processed = models.BooleanField(default=False, verbose_name="İşlendi mi?")

    class Meta:
        verbose_name = "Operasyon Öğesi"
        verbose_name_plural = "Operasyon Öğeleri"
        ordering = ['pick_time']

    def __str__(self):
        day_str = self.day or "Day not set"
        operation_type_str = self.operation_type or "Operation Type not set"
        return f"{day_str} - {operation_type_str}"

class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Açık'),
        ('in_progress', 'İşlemde'),
        ('closed', 'Kapalı'),
    )

    TITLE_CHOICES = (
        ('login_issue', 'Giriş Sorunu'),
        ('payment_issue', 'Ödeme Sorunu'),
        ('bug_report', 'Hata Bildirimi'),
        ('account_info', 'Hesap Bilgisi Sorgulama'),
        ('suggestion', 'Öneri'),
        ('training', 'Eğitim'),
    )
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="destek_kayıtları")
    user = models.ForeignKey(Personel, verbose_name="Kaydı Açan", on_delete=models.SET_NULL, blank=True, null=True, related_name="destek_kayıtları")
    title = models.CharField(max_length=100, choices=TITLE_CHOICES, default='login_issue', verbose_name="Başlık", db_index=True)
    description = models.TextField(verbose_name="Açıklama")
    cevap = models.TextField(verbose_name="Cevap", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="Durum", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Zamanı", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Zamanı")

    class Meta:
        verbose_name = "Destek Kaydı"
        verbose_name_plural = "Destek Kayıtları"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_title_display()} ({self.get_status_display()})"

class Notification(models.Model):
    JOB_CHOICES = (
        ('Herkes', 'Herkes'),
        ('Satış Personeli', 'Satış Personeli'),
        ('Operasyon Şefi', 'Operasyon Şefi'),
        ('Yönetim', 'Yönetim'),
        ('Muhasebe', 'Muhasebe'),
    )
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, blank=True, null=True, related_name="bildirimler")
    title = models.CharField(max_length=255, verbose_name="Başlık")
    message = models.TextField(verbose_name="Mesaj")
    sender = models.ForeignKey(Personel, related_name='gönderilen_bildirimler', on_delete=models.CASCADE, verbose_name="Gönderen")
    recipients_group = models.CharField(max_length=20, choices=JOB_CHOICES, verbose_name="Mesaj Grupları", default="Herkes", db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Bildirim"
        verbose_name_plural = "Bildirimler"
        ordering = ['-timestamp']

    def __str__(self):
        return f"From {self.sender} to multiple recipients - {self.title}"

class NotificationReceipt(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='makbuzlar', verbose_name="Bildirim")
    recipient = models.ForeignKey(Personel, on_delete=models.CASCADE, related_name='alınan_bildirimler', verbose_name="Alıcı")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Okunma Zamanı", db_index=True)  # Eğer null ise, henüz okunmamıştır.

    class Meta:
        unique_together = ('notification', 'recipient')  # Her bir personel için bir bildirimi bir kere kaydetmek.
        verbose_name = "Bildirim Alındı"
        verbose_name_plural = "Bildirim Alındıları"

    def __str__(self):
        read_status = 'Okundu' if self.read_at else 'Okunmadı'
        return f"{self.notification.title} - {self.recipient.user.username} - {read_status}"

class ExchangeRate(models.Model):
    usd_to_try = models.FloatField(verbose_name='USD/TRY')
    usd_to_eur = models.FloatField(verbose_name='USD/EUR') 
    usd_to_rmb = models.FloatField(verbose_name='USD/RMB')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Döviz Kuru'
        verbose_name_plural = 'Döviz Kurları'
        ordering = ['-created_at']

    def __str__(self):
        return f"Döviz Kuru ({self.created_at})"

class Smsgonder(models.Model):
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="mesajlar")
    user = models.ForeignKey(Personel, verbose_name="Gönderen", on_delete=models.SET_NULL, related_name="gönderilen_mesajlar", blank=True, null=True)
    staff = models.ManyToManyField(Personel, blank=True, verbose_name="Alıcılar", related_name="alınan_mesajlar")
    message = models.TextField(verbose_name="Mesaj")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Zamanı", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Zamanı")
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Mesaj Logu"
        verbose_name_plural = "Mesaj Logları"
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f"{self.user.user.get_full_name()} ({self.message})"
        return f"Anonim Gönderici ({self.message})"

class Cari(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Gelir'),
        ('expense', 'Gider'),
    )

    GELIR_KAYNAK = (
        ('Truzim', 'Truzim'),
    )
    GIDER_KAYNAK = (
        ('Arac', 'Araç Ödemesi'),
        ('Aktivite', 'Aktivite Ödemesi'),
        ('Rehber', 'Rehber Ödemesi'),
        ('Otel', 'Otel Ödemesi'),
        ('Müze', 'Müze Ödemeleri'),
        ('Maas', 'Maaş Ödemesi'),
        ('Fatura', 'Fatura Ödemeleri'),
        ('Vergi', 'Vergi Ödemeleri'),
        ('Diğer', 'Diğer Ödemeler'),
    )
    company = models.ForeignKey(Sirket, verbose_name="Şirket", on_delete=models.CASCADE, related_name="cari_hareketleri")
    description = models.TextField(verbose_name="Açıklama", blank=True, null=True)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES, verbose_name="İşlem Türü", db_index=True)
    income = models.CharField(max_length=30, choices=GELIR_KAYNAK, verbose_name="Gelir Kaynağı", blank=True, null=True, db_index=True)
    expense = models.CharField(max_length=30, choices=GIDER_KAYNAK, verbose_name="Gider Kaynağı", blank=True, null=True, db_index=True)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True, verbose_name="Fiş/Makbuz")
    price = models.DecimalField(verbose_name="Tutar", max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, verbose_name="Para Birimi", default="TL")
    buyer_company = models.ForeignKey(Buyercompany, verbose_name="Firmalar", related_name="cari_gelirler", on_delete=models.SET_NULL, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, verbose_name="Araç Tedarikçisi", related_name="cari_giderler", on_delete=models.SET_NULL, blank=True, null=True)
    hotel = models.ForeignKey(Hotel, verbose_name="Oteller", related_name="cari_giderler", on_delete=models.SET_NULL, blank=True, null=True)
    guide = models.ForeignKey(Guide, verbose_name="Rehberler", related_name="cari_giderler", on_delete=models.SET_NULL, blank=True, null=True)
    activity_supplier = models.ForeignKey(Activitysupplier, verbose_name="Aktivite Tedarikçisi", related_name="cari_giderler", on_delete=models.SET_NULL, blank=True, null=True)
    created_staff = models.ForeignKey(Personel, verbose_name="Oluşturan Personel", related_name="oluşturduğu_işlemler", on_delete=models.SET_NULL, blank=True, null=True)
    create_date = models.DateTimeField(verbose_name="Oluşturulma Tarihi", auto_now=False, auto_now_add=True, db_index=True)
    update_date = models.DateTimeField(verbose_name="Güncelleme Tarihi", auto_now=True, auto_now_add=False)
    is_delete = models.BooleanField(verbose_name="Silindi mi?", default=False, db_index=True)

    class Meta:
        verbose_name = "Cari İşlem"
        verbose_name_plural = "Cari İşlemler"
        ordering = ['-create_date']

    def __str__(self):
        transaction_type_display = "Gelir" if self.transaction_type == "income" else "Gider"
        return f"{transaction_type_display}: {self.price} {self.currency} ({self.create_date})"
