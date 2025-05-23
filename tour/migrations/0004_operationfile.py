# Generated by Django 5.2 on 2025-05-06 17:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tour', '0003_delete_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperationFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_type', models.CharField(choices=[('Çince Operasyon', 'Çince Operasyon'), ('Aktivite Belgeleri', 'Aktivite Belgeleri'), ('Rehber Belgeleri', 'Rehber Belgeleri'), ('Araç Görselleri', 'Araç Görselleri'), ('Araç Temizlik', 'Araç Temizlik'), ('Otopark', 'Otopark'), ('Yemek Fişi', 'Yemek Fişi'), ('Otel Dekont', 'Otel Dekont'), ('Müze Dekont', 'Müze Dekont'), ('Konfirme Mektubu', 'Konfirme Mektubu'), ('Diğer Belgeler', 'Diğer Belgeler')], max_length=255, verbose_name='Dosya Tipi')),
                ('file', models.FileField(upload_to='operation_files/', verbose_name='Dosya')),
                ('is_delete', models.BooleanField(db_index=True, default=False, verbose_name='Silindi mi?')),
                ('operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='tour.operation', verbose_name='Operasyon')),
                ('operation_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='tour.operationitem', verbose_name='Operasyon Öğesi')),
            ],
            options={
                'verbose_name': 'Operasyon Dosyası',
                'verbose_name_plural': 'Operasyon Dosyaları',
            },
        ),
    ]
