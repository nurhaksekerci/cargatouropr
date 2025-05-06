from django.contrib import admin
from .models import *


@admin.register(Sirket)
class SirketAdmin(admin.ModelAdmin):
    list_display = ('name', 'statu', 'start', 'finish', 'is_active', 'is_delete')
    list_filter = ('statu', 'is_active', 'is_delete')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'


@admin.register(Personel)
class PersonelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'company', 'job', 'phone', 'is_active', 'is_delete')
    list_filter = ('company', 'job', 'is_active', 'is_delete', 'gender')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    raw_id_fields = ('user', 'company')



@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('route', 'start_city', 'finish_city', 'company', 'is_delete')
    list_filter = ('company', 'is_delete', 'start_city', 'finish_city')
    search_fields = ('route', 'start_city', 'finish_city')


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('route', 'start_city', 'finish_city', 'company', 'is_delete')
    list_filter = ('company', 'is_delete', 'start_city', 'finish_city')
    search_fields = ('route', 'start_city', 'finish_city')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'capacity', 'company')
    list_filter = ('company', 'is_delete')
    search_fields = ('vehicle',)


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'phone', 'price', 'currency')
    list_filter = ('company', 'is_delete', 'city', 'currency')
    search_fields = ('name', 'phone', 'doc_no', 'mail')


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'one_person', 'two_person', 'currency')
    list_filter = ('company', 'is_delete', 'city', 'currency')
    search_fields = ('name', 'city', 'mail')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'company')
    list_filter = ('company', 'is_delete', 'city')
    search_fields = ('name', 'city')


@admin.register(Museum)
class MuseumAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'price', 'currency')
    list_filter = ('company', 'is_delete', 'city', 'currency')
    search_fields = ('name', 'city', 'contact')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'company')
    list_filter = ('company', 'is_delete')
    search_fields = ('name', 'contact')


@admin.register(Activitysupplier)
class ActivitysupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'company')
    list_filter = ('company', 'is_delete')
    search_fields = ('name', 'contact')


@admin.register(Cost)
class CostAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'tour', 'transfer', 'car', 'minibus', 'currency')
    list_filter = ('company', 'is_delete', 'currency')
    search_fields = ('supplier__name', 'tour__route', 'transfer__route')
    autocomplete_fields = ('supplier', 'tour', 'transfer', 'company')


@admin.register(Activitycost)
class ActivitycostAdmin(admin.ModelAdmin):
    list_display = ('activity', 'supplier', 'price', 'currency')
    list_filter = ('company', 'is_delete', 'currency')
    search_fields = ('activity__name', 'supplier__name')
    autocomplete_fields = ('activity', 'supplier', 'company')


@admin.register(Buyercompany)
class BuyercompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'contact')
    list_filter = ('company', 'is_delete')
    search_fields = ('name', 'short_name', 'contact')


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('staff', 'action', 'ip_address', 'timestamp')
    list_filter = ('company', 'timestamp')
    search_fields = ('staff__user__username', 'action', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('staff', 'action', 'ip_address', 'browser_info', 'timestamp')


class OperationdayInline(admin.TabularInline):
    model = Operationday
    extra = 0


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'buyer_company', 'start', 'finish', 'sold', 'number_passengers')
    list_filter = ('company', 'sold', 'payment_type', 'payment_channel', 'is_delete')
    search_fields = ('ticket', 'buyer_company__name', 'passenger_info')
    date_hierarchy = 'start'
    autocomplete_fields = ('buyer_company', 'selling_staff', 'follow_staff', 'company')
    inlines = [OperationdayInline]
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'ticket', 'buyer_company', 'start', 'finish')
        }),
        ('Personel Bilgisi', {
            'fields': ('selling_staff', 'follow_staff')
        }),
        ('Yolcu Bilgileri', {
            'fields': ('passenger_info', 'number_passengers')
        }),
        ('Ödeme Bilgileri', {
            'fields': ('payment_type', 'payment_channel', 'remaining_payment', 'sold')
        }),
        ('Satış Fiyatları', {
            'fields': ('tl_sales_price', 'usd_sales_price', 'eur_sales_price', 'rbm_sales_price', 'total_sales_price')
        }),
        ('Maliyet Fiyatları', {
            'fields': ('tl_cost_price', 'usd_cost_price', 'eur_cost_price', 'rbm_cost_price', 'total_cost_price')
        }),
        ('Aktivite Fiyatları', {
            'fields': ('tl_activity_price', 'usd_activity_price', 'eur_activity_price', 'rbm_activity_price')
        }),
        ('Diğer', {
            'fields': ('is_delete',)
        }),
    )


class OperationitemInline(admin.TabularInline):
    model = Operationitem
    extra = 0
    fields = ('operation_type', 'pick_time', 'release_time', 'pick_location', 'release_location')


@admin.register(Operationday)
class OperationdayAdmin(admin.ModelAdmin):
    list_display = ('operation', 'date', 'day_number')
    list_filter = ('company', 'is_delete', 'date')
    search_fields = ('operation__ticket', 'day_number')
    date_hierarchy = 'date'
    autocomplete_fields = ('operation', 'company')
    inlines = [OperationitemInline]


@admin.register(Operationitem)
class OperationitemAdmin(admin.ModelAdmin):
    list_display = ('day', 'operation_type', 'pick_time', 'release_time')
    list_filter = ('company', 'operation_type', 'is_delete', 'day__date', 'is_processed')
    search_fields = ('day__operation__ticket', 'pick_location', 'release_location')
    autocomplete_fields = ('day', 'tour', 'transfer', 'vehicle', 'supplier', 'hotel', 'activity', 'guide', 'company')
    filter_horizontal = ('new_museum',)
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'day', 'operation_type', 'pick_time', 'release_time', 'pick_location', 'release_location')
        }),
        ('Tur & Transfer', {
            'fields': ('tour', 'transfer', 'cost')
        }),
        ('Araç Bilgileri', {
            'fields': ('vehicle', 'supplier', 'manuel_vehicle_price', 'auto_vehicle_price', 'vehicle_price', 
                      'vehicle_sell_price', 'vehicle_currency', 'vehicle_sell_currency', 'driver', 'driver_phone', 'plaka')
        }),
        ('Otel Bilgileri', {
            'fields': ('hotel', 'room_type', 'hotel_price', 'hotel_sell_price', 'hotel_currency', 
                      'hotel_sell_currency', 'hotel_payment')
        }),
        ('Aktivite Bilgileri', {
            'fields': ('activity', 'activity_supplier', 'activity_cost', 'activity_price', 'manuel_activity_price', 
                      'auto_activity_price', 'activity_sell_price', 'activity_currency', 'activity_sell_currency', 'activity_payment')
        }),
        ('Müze Bilgileri', {
            'fields': ('new_museum', 'museum_person', 'museum_price', 'museum_sell_price', 'museum_currency', 
                      'museum_sell_currency', 'museum_payment')
        }),
        ('Rehber Bilgileri', {
            'fields': ('guide', 'guide_var', 'guide_price', 'guide_sell_price', 'guide_currency', 'guide_sell_currency')
        }),
        ('Maliyet Bilgileri', {
            'fields': ('tl_cost_price', 'usd_cost_price', 'eur_cost_price', 'rmb_cost_price')
        }),
        ('Diğer', {
            'fields': ('other_price', 'other_currency', 'other_sell_price', 'other_sell_currency', 'description', 'is_processed', 'is_delete')
        }),
    )


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at')
    list_filter = ('company', 'status', 'title')
    search_fields = ('description', 'cevap', 'user__user__username')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('user', 'company')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'sender', 'recipients_group', 'timestamp')
    list_filter = ('company', 'recipients_group')
    search_fields = ('title', 'message', 'sender__user__username')
    date_hierarchy = 'timestamp'
    autocomplete_fields = ('sender', 'company')


@admin.register(NotificationReceipt)
class NotificationReceiptAdmin(admin.ModelAdmin):
    list_display = ('notification', 'recipient', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('notification__title', 'recipient__user__username')
    date_hierarchy = 'read_at'
    autocomplete_fields = ('notification', 'recipient')


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('usd_to_try', 'usd_to_eur', 'usd_to_rmb', 'created_at')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


@admin.register(Smsgonder)
class SmsgonderAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    list_filter = ('company', 'is_delete')
    search_fields = ('user__user__username', 'message')
    date_hierarchy = 'created_at'
    filter_horizontal = ('staff',)
    autocomplete_fields = ('user', 'company')


@admin.register(Cari)
class CariAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'income', 'expense', 'price', 'currency', 'created_staff', 'create_date')
    list_filter = ('company', 'transaction_type', 'income', 'expense', 'currency', 'is_delete')
    search_fields = ('description', 'price', 'buyer_company__name', 'supplier__name')
    date_hierarchy = 'create_date'
    autocomplete_fields = ('buyer_company', 'supplier', 'hotel', 'guide', 'activity_supplier', 'created_staff', 'company')
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'description', 'transaction_type', 'price', 'currency')
        }),
        ('Gelir Bilgileri', {
            'fields': ('income', 'buyer_company')
        }),
        ('Gider Bilgileri', {
            'fields': ('expense', 'supplier', 'hotel', 'guide', 'activity_supplier')
        }),
        ('Diğer', {
            'fields': ('receipt', 'created_staff', 'is_delete')
        }),
    )
