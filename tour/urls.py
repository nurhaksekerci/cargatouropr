from django.urls import path
from . import views

app_name = 'tour'

urlpatterns = [
    # Giriş ve Çıkış
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:username>/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),

    path('', views.dashboard, name='dashboard'),

    # Aktivite Logları
    path('aktivite-kayitlarim/', views.my_user_activity_log, name='my_activity_logs'),

    # Operasyon
    path('operasyon/ekle/', views.operation_create, name='operation_create'),
    path('operasyon/<int:pk>/', views.operation_detail, name='operation_detail'),
    path('operasyon-item/<int:pk>/', views.operationitem_edit, name='operationitem_edit'),
    path('operasyon-toggle/<int:pk>/', views.operation_toggle_view, name='operation_toggle'),
    path('operasyon-edit/<int:pk>/', views.operation_edit, name='operation_edit'),

    # Operasyon İtem ekleme
    path('operasyon-item-ekle/<int:day_id>/', views.operationday_item_create, name='operationday_item_create'),

    path('operasyon-silinmis-listesi/', views.operation_deleted_list, name='operation_deleted_list'),
    path('operasyon-gün-toggle/<int:pk>/', views.operationday_toggle_view, name='operationday_toggle'),

    # Operasyon İtem silme
    path('operasyon-item-toggle/<int:pk>/', views.operationitem_toggle_view, name='operationitem_toggle'),

    # Operasyon Dosyası ekleme
    path('operasyon-dosyasi-ekle/<int:pk>/', views.operationfile_create, name='operationfile_create'),
    path('operasyon-item-dosyasi-ekle/<int:pk>/', views.operationitemfile_create, name='operationitemfile_create'),

    # İş Listesi
    path('is-listem/', views.my_job_list, name='my_job_list'),
    path('is-listesi/', views.job_list, name='job_list'),

    # Generic list view için URL pattern
    path('list/<str:model_name>/', views.generic_list, name='generic_list'),
    # Generic create view için URL pattern
    path('create/<str:model_name>/', views.generic_create, name='generic_create'),
    # Generic update view için URL pattern
    path('update/<str:model_name>/<int:pk>/', views.generic_update, name='generic_update'),
    # Generic delete view için URL pattern
    path('delete/<str:model_name>/<int:pk>/', views.generic_delete, name='generic_delete'),
    # Generic deleted list view için URL pattern
    path('deleted-list/<str:model_name>/', views.generic_deleted_list, name='generic_deleted_list'),
    # Generic restore view için URL pattern
    path('restore/<str:model_name>/<int:pk>/', views.restore_object, name='restore_object'),
    
    # Aşağıda her model için kısa yollar ekleyebilirsiniz
    # List views
    path('sirketler/', views.generic_list, {'model_name': 'sirket'}, name='sirket_list'),
    path('turlar/', views.generic_list, {'model_name': 'tour'}, name='tour_list'),
    path('transferler/', views.generic_list, {'model_name': 'transfer'}, name='transfer_list'),
    path('araclar/', views.generic_list, {'model_name': 'vehicle'}, name='vehicle_list'),
    path('rehberler/', views.generic_list, {'model_name': 'guide'}, name='guide_list'),
    path('oteller/', views.generic_list, {'model_name': 'hotel'}, name='hotel_list'),
    path('aktiviteler/', views.generic_list, {'model_name': 'activity'}, name='activity_list'),
    path('muzeler/', views.generic_list, {'model_name': 'museum'}, name='museum_list'),
    path('tedarikciler/', views.generic_list, {'model_name': 'supplier'}, name='supplier_list'),
    path('aktivite-tedarikcileri/', views.generic_list, {'model_name': 'activitysupplier'}, name='activitysupplier_list'),
    path('maliyetler/', views.generic_list, {'model_name': 'cost'}, name='cost_list'),
    path('aktivite-maliyetleri/', views.generic_list, {'model_name': 'activitycost'}, name='activitycost_list'),
    path('alici-firmalar/', views.generic_list, {'model_name': 'buyercompany'}, name='buyercompany_list'),
    path('personeller/', views.generic_list, {'model_name': 'personel'}, name='personel_list'),
    
    # Deleted List views
    path('sirketler/silinmis/', views.generic_deleted_list, {'model_name': 'sirket'}, name='sirket_deleted_list'),
    path('turlar/silinmis/', views.generic_deleted_list, {'model_name': 'tour'}, name='tour_deleted_list'),
    path('transferler/silinmis/', views.generic_deleted_list, {'model_name': 'transfer'}, name='transfer_deleted_list'),
    path('araclar/silinmis/', views.generic_deleted_list, {'model_name': 'vehicle'}, name='vehicle_deleted_list'),
    path('rehberler/silinmis/', views.generic_deleted_list, {'model_name': 'guide'}, name='guide_deleted_list'),
    path('oteller/silinmis/', views.generic_deleted_list, {'model_name': 'hotel'}, name='hotel_deleted_list'),
    path('aktiviteler/silinmis/', views.generic_deleted_list, {'model_name': 'activity'}, name='activity_deleted_list'),
    path('muzeler/silinmis/', views.generic_deleted_list, {'model_name': 'museum'}, name='museum_deleted_list'),
    path('tedarikciler/silinmis/', views.generic_deleted_list, {'model_name': 'supplier'}, name='supplier_deleted_list'),
    path('aktivite-tedarikcileri/silinmis/', views.generic_deleted_list, {'model_name': 'activitysupplier'}, name='activitysupplier_deleted_list'),
    path('maliyetler/silinmis/', views.generic_deleted_list, {'model_name': 'cost'}, name='cost_deleted_list'),
    path('aktivite-maliyetleri/silinmis/', views.generic_deleted_list, {'model_name': 'activitycost'}, name='activitycost_deleted_list'),
    path('alici-firmalar/silinmis/', views.generic_deleted_list, {'model_name': 'buyercompany'}, name='buyercompany_deleted_list'),
    path('personeller/silinmis/', views.generic_deleted_list, {'model_name': 'personel'}, name='personel_deleted_list'),
    
    # Create views
    path('sirket/ekle/', views.generic_create, {'model_name': 'sirket'}, name='sirket_create'),
    path('tur/ekle/', views.generic_create, {'model_name': 'tour'}, name='tour_create'),
    path('transfer/ekle/', views.generic_create, {'model_name': 'transfer'}, name='transfer_create'),
    path('arac/ekle/', views.generic_create, {'model_name': 'vehicle'}, name='vehicle_create'),
    path('rehber/ekle/', views.generic_create, {'model_name': 'guide'}, name='guide_create'),
    path('otel/ekle/', views.generic_create, {'model_name': 'hotel'}, name='hotel_create'),
    path('aktivite/ekle/', views.generic_create, {'model_name': 'activity'}, name='activity_create'),
    path('muze/ekle/', views.generic_create, {'model_name': 'museum'}, name='museum_create'),
    path('tedarikci/ekle/', views.generic_create, {'model_name': 'supplier'}, name='supplier_create'),
    path('aktivite-tedarikci/ekle/', views.generic_create, {'model_name': 'activitysupplier'}, name='activitysupplier_create'),
    path('maliyet/ekle/', views.generic_create, {'model_name': 'cost'}, name='cost_create'),
    path('aktivite-maliyet/ekle/', views.generic_create, {'model_name': 'activitycost'}, name='activitycost_create'),
    path('alici-firma/ekle/', views.generic_create, {'model_name': 'buyercompany'}, name='buyercompany_create'),
    path('personel/ekle/', views.generic_create, {'model_name': 'personel'}, name='personel_create'),
    
    # Update views
    path('sirket/duzenle/<int:pk>/', views.generic_update, {'model_name': 'sirket'}, name='sirket_update'),
    path('tur/duzenle/<int:pk>/', views.generic_update, {'model_name': 'tour'}, name='tour_update'),
    path('transfer/duzenle/<int:pk>/', views.generic_update, {'model_name': 'transfer'}, name='transfer_update'),
    path('arac/duzenle/<int:pk>/', views.generic_update, {'model_name': 'vehicle'}, name='vehicle_update'),
    path('rehber/duzenle/<int:pk>/', views.generic_update, {'model_name': 'guide'}, name='guide_update'),
    path('otel/duzenle/<int:pk>/', views.generic_update, {'model_name': 'hotel'}, name='hotel_update'),
    path('aktivite/duzenle/<int:pk>/', views.generic_update, {'model_name': 'activity'}, name='activity_update'),
    path('muze/duzenle/<int:pk>/', views.generic_update, {'model_name': 'museum'}, name='museum_update'),
    path('tedarikci/duzenle/<int:pk>/', views.generic_update, {'model_name': 'supplier'}, name='supplier_update'),
    path('aktivite-tedarikci/duzenle/<int:pk>/', views.generic_update, {'model_name': 'activitysupplier'}, name='activitysupplier_update'),
    path('maliyet/duzenle/<int:pk>/', views.generic_update, {'model_name': 'cost'}, name='cost_update'),
    path('aktivite-maliyet/duzenle/<int:pk>/', views.generic_update, {'model_name': 'activitycost'}, name='activitycost_update'),
    path('alici-firma/duzenle/<int:pk>/', views.generic_update, {'model_name': 'buyercompany'}, name='buyercompany_update'),
    path('personel/duzenle/<int:pk>/', views.generic_update, {'model_name': 'personel'}, name='personel_update'),
    
    # Delete views
    path('sirket/sil/<int:pk>/', views.generic_delete, {'model_name': 'sirket'}, name='sirket_delete'),
    path('tur/sil/<int:pk>/', views.generic_delete, {'model_name': 'tour'}, name='tour_delete'),
    path('transfer/sil/<int:pk>/', views.generic_delete, {'model_name': 'transfer'}, name='transfer_delete'),
    path('arac/sil/<int:pk>/', views.generic_delete, {'model_name': 'vehicle'}, name='vehicle_delete'),
    path('rehber/sil/<int:pk>/', views.generic_delete, {'model_name': 'guide'}, name='guide_delete'),
    path('otel/sil/<int:pk>/', views.generic_delete, {'model_name': 'hotel'}, name='hotel_delete'),
    path('aktivite/sil/<int:pk>/', views.generic_delete, {'model_name': 'activity'}, name='activity_delete'),
    path('muze/sil/<int:pk>/', views.generic_delete, {'model_name': 'museum'}, name='museum_delete'),
    path('tedarikci/sil/<int:pk>/', views.generic_delete, {'model_name': 'supplier'}, name='supplier_delete'),
    path('aktivite-tedarikci/sil/<int:pk>/', views.generic_delete, {'model_name': 'activitysupplier'}, name='activitysupplier_delete'),
    path('maliyet/sil/<int:pk>/', views.generic_delete, {'model_name': 'cost'}, name='cost_delete'),
    path('aktivite-maliyet/sil/<int:pk>/', views.generic_delete, {'model_name': 'activitycost'}, name='activitycost_delete'),
    path('alici-firma/sil/<int:pk>/', views.generic_delete, {'model_name': 'buyercompany'}, name='buyercompany_delete'),
    path('personel/sil/<int:pk>/', views.generic_delete, {'model_name': 'personel'}, name='personel_delete'),
    
    # Restore views
    path('sirket/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'sirket'}, name='sirket_restore'),
    path('tur/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'tour'}, name='tour_restore'),
    path('transfer/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'transfer'}, name='transfer_restore'),
    path('arac/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'vehicle'}, name='vehicle_restore'),
    path('rehber/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'guide'}, name='guide_restore'),
    path('otel/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'hotel'}, name='hotel_restore'),
    path('aktivite/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'activity'}, name='activity_restore'),
    path('muze/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'museum'}, name='museum_restore'),
    path('tedarikci/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'supplier'}, name='supplier_restore'),
    path('aktivite-tedarikci/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'activitysupplier'}, name='activitysupplier_restore'),
    path('maliyet/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'cost'}, name='cost_restore'),
    path('aktivite-maliyet/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'activitycost'}, name='activitycost_restore'),
    path('alici-firma/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'buyercompany'}, name='buyercompany_restore'),
    path('personel/geri-getir/<int:pk>/', views.restore_object, {'model_name': 'personel'}, name='personel_restore'),

    # Operasyon URL'leri
    path('operasyon-listesi/', views.operation_list, name='operation_list'),
    path('operationitem/deleted/<int:operation_id>/', views.operationitem_deleted_list, name='operationitem_deleted_list'),
]
