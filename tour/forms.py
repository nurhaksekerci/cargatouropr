from django import forms
from django.utils.text import slugify
from .models import (
    OperationFile, Sirket, Tour, Transfer, Vehicle, Guide, Hotel, 
    Activity, Museum, Supplier, Activitysupplier, 
    Cost, Activitycost, Buyercompany, Personel, Operation,
    Operationitem, Operationday
)
from django.contrib.auth.models import User
from django.forms import modelformset_factory, inlineformset_factory, BaseInlineFormSet

class SirketForm(forms.ModelForm):
    class Meta:
        model = Sirket
        exclude = ['is_delete', 'slug', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'finish': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'statu': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = self.generate_unique_slug(instance)
        if commit:
            instance.save()
        return instance
    
    def generate_unique_slug(self, instance):
        original_slug = slugify(instance.name.replace('ı', 'i').replace('İ', 'I'))
        slug = original_slug
        counter = 1
        while Sirket.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        return slug

class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        exclude = ['company', 'is_delete', 'created_at', 'updated_at']
        widgets = {
            'route': forms.TextInput(attrs={'class': 'form-control'}),
            'start_city': forms.Select(attrs={'class': 'form-select'}),
            'finish_city': forms.Select(attrs={'class': 'form-select'}),
        }

class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        exclude = ['company', 'is_delete', 'created_at', 'updated_at']
        widgets = {
            'route': forms.TextInput(attrs={'class': 'form-control'}),
            'start_city': forms.Select(attrs={'class': 'form-select'}),
            'finish_city': forms.Select(attrs={'class': 'form-select'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        exclude = ['company', 'is_delete']
        widgets = {
            'vehicle': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class GuideForm(forms.ModelForm):
    class Meta:
        model = Guide
        exclude = ['company', 'is_delete']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'doc_no': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'mail': forms.EmailInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }

class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        exclude = ['company', 'is_delete']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'mail': forms.EmailInput(attrs={'class': 'form-control'}),
            'one_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'two_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tree_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'finish': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ['company', 'is_delete']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
        }

class MuseumForm(forms.ModelForm):
    class Meta:
        model = Museum
        exclude = ['company', 'is_delete']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        exclude = ['company', 'is_delete']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ActivitysupplierForm(forms.ModelForm):
    class Meta:
        model = Activitysupplier
        exclude = ['company', 'is_delete']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CostForm(forms.ModelForm):
    class Meta:
        model = Cost
        exclude = ['company', 'is_delete']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'tour': forms.Select(attrs={'class': 'form-select'}),
            'transfer': forms.Select(attrs={'class': 'form-select'}),
            'car': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'minivan': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'minibus': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'midibus': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bus': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }

class ActivitycostForm(forms.ModelForm):
    class Meta:
        model = Activitycost
        exclude = ['company', 'is_delete']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }

class BuyercompanyForm(forms.ModelForm):
    class Meta:
        model = Buyercompany
        exclude = ['company', 'is_delete']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '5'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PersonelForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Ad", 
        max_length=30, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Soyad", 
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="E-posta", 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        label="Kullanıcı Adı", 
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label="Şifre", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label="Şifre (Tekrar)", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Personel
        fields = ['phone', 'gender', 'job', 'is_active']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'job': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu e-posta adresi zaten kullanılıyor.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Şifreler eşleşmiyor.")
        
        return cleaned_data
    
    def save(self, commit=True, company=None):
        # Formdan veriler alınıyor
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password1')
        
        # Önce User nesnesi oluşturuluyor
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Sonra Personel nesnesi oluşturuluyor
        personel = super().save(commit=False)
        personel.user = user
        
        # Şirket bilgisi varsa atanıyor
        if company:
            personel.company = company
        
        if commit:
            personel.save()
        
        return personel

class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ['ticket', 'buyer_company', 'follow_staff', 'start', 'finish', 'passenger_info', 'number_passengers', 'payment_type', 'payment_channel', 'remaining_payment', 'tl_sales_price', 'usd_sales_price', 'eur_sales_price', 'rbm_sales_price']
        widgets = {
            'ticket': forms.TextInput(attrs={'class': 'form-control'}),
            'follow_staff': forms.Select(attrs={'class': 'form-select'}),
            'buyer_company': forms.Select(attrs={'class': 'form-select'}),
            'start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'finish': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'passenger_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'number_passengers': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_channel': forms.Select(attrs={'class': 'form-select'}),
            'remaining_payment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tl_sales_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usd_sales_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'eur_sales_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rbm_sales_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['follow_staff'].queryset = Personel.objects.filter(company=company, is_active=True)
            self.fields['buyer_company'].queryset = Buyercompany.objects.filter(company=company, is_delete=False)
        else:
            self.fields['follow_staff'].queryset = Personel.objects.filter(is_active=True)
            self.fields['buyer_company'].queryset = Buyercompany.objects.filter(is_delete=False)
        
        # Tarih alanları için mevcut değerleri uygun formatta ayarla
        if self.instance and self.instance.pk:
            # Eğer bir instance varsa ve veritabanından geliyorsa (pk != None)
            if self.instance.start:
                self.initial['start'] = self.instance.start.strftime('%Y-%m-%d')
            if self.instance.finish:
                self.initial['finish'] = self.instance.finish.strftime('%Y-%m-%d')
    
    def save(self, commit=True, company=None):
        instance = super().save(commit=False)
        
        # Şirket bilgisi varsa atanıyor
        if company:
            instance.company = company
        
        # Toplam satış fiyatını hesapla
        instance.total_sales_price = (
            instance.tl_sales_price + 
            instance.usd_sales_price + 
            instance.eur_sales_price + 
            instance.rbm_sales_price
        )
        
        # Toplam maliyet fiyatını hesapla
        instance.total_cost_price = (
            instance.tl_cost_price + 
            instance.usd_cost_price + 
            instance.eur_cost_price + 
            instance.rbm_cost_price
        )
        
        if commit:
            instance.save()
        
        return instance

class OperationItemForm(forms.ModelForm):
    """
    Operasyon öğesi düzenleme formu - performans için optimize edilmiş
    """
    class Meta:
        model = Operationitem
        fields = [
            'operation_type', 'pick_time',
            'pick_location', 'release_location', 'tour', 'transfer', 
            'vehicle', 'supplier', 'manuel_vehicle_price', 'driver', 'driver_phone', 'plaka', 
            'hotel', 'room_type', 'hotel_payment', 'hotel_price', 'hotel_currency',
            'activity', 'activity_supplier', 'activity_payment', 'manuel_activity_price', 'activity_currency',
            'new_museum', 'museum_person', 'museum_payment', 'museum_price', 'museum_currency',
            'guide', 'guide_price', 'guide_currency', 'guide_var', 'description',
        ]
        widgets = {
            'operation_type': forms.Select(attrs={'class': 'form-control'}),
            'pick_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'pick_location': forms.TextInput(attrs={'class': 'form-control'}),
            'release_location': forms.TextInput(attrs={'class': 'form-control'}),
            'tour': forms.Select(attrs={'class': 'form-control'}),
            'transfer': forms.Select(attrs={'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'manuel_vehicle_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'driver': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'plaka': forms.TextInput(attrs={'class': 'form-control'}),
            'hotel': forms.Select(attrs={'class': 'form-control'}),
            'room_type': forms.TextInput(attrs={'class': 'form-control'}),
            'hotel_payment': forms.Select(attrs={'class': 'form-control'}),
            'hotel_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hotel_currency': forms.Select(attrs={'class': 'form-control'}),
            'activity': forms.Select(attrs={'class': 'form-control'}),
            'activity_supplier': forms.Select(attrs={'class': 'form-control'}),
            'activity_payment': forms.Select(attrs={'class': 'form-control'}),
            'manuel_activity_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'guide': forms.Select(attrs={'class': 'form-control'}),
            'guide_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'guide_var': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'new_museum': forms.SelectMultiple(attrs={'class': 'form-control', 'multiple': 'multiple'}),
            'museum_person': forms.NumberInput(attrs={'class': 'form-control'}),
            'museum_payment': forms.Select(attrs={'class': 'form-control'}),
            'museum_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'museum_currency': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['new_museum'].queryset = Museum.objects.filter(company=company, is_delete=False)
            self.fields['vehicle'].queryset = Vehicle.objects.filter(company=company, is_delete=False)
            self.fields['supplier'].queryset = Supplier.objects.filter(company=company, is_delete=False)
            self.fields['hotel'].queryset = Hotel.objects.filter(company=company, is_delete=False)
            self.fields['activity'].queryset = Activity.objects.filter(company=company, is_delete=False)
            self.fields['activity_supplier'].queryset = Activitysupplier.objects.filter(company=company, is_delete=False)
            self.fields['guide'].queryset = Guide.objects.filter(company=company, is_delete=False)
            self.fields['transfer'].queryset = Transfer.objects.filter(company=company, is_delete=False)
            self.fields['tour'].queryset = Tour.objects.filter(company=company, is_delete=False)
        else:
            self.fields['new_museum'].queryset = Museum.objects.filter(is_delete=False)
            self.fields['vehicle'].queryset = Vehicle.objects.filter(is_delete=False)
            self.fields['supplier'].queryset = Supplier.objects.filter(is_delete=False)
            self.fields['hotel'].queryset = Hotel.objects.filter(is_delete=False)
            self.fields['activity'].queryset = Activity.objects.filter(is_delete=False)
            self.fields['activity_supplier'].queryset = Activitysupplier.objects.filter(is_delete=False)
            self.fields['guide'].queryset = Guide.objects.filter(is_delete=False)
            self.fields['transfer'].queryset = Transfer.objects.filter(is_delete=False)
            self.fields['tour'].queryset = Tour.objects.filter(is_delete=False)


class OperationFileForm(forms.ModelForm):
    class Meta:
        model = OperationFile
        fields = ['file_type', 'file']
        widgets = {
            'file_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }



