import json

# Orijinal dump dosyasının adı
input_file = 'Museum_dump.json'
# Temizlenmiş çıktının yazılacağı yeni dosya
output_file = 'Museum_dump_clean.json'

# JSON dosyasını oku
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Her kayıttan 'new_city' alanını sil
for obj in data:
    if 'fields' in obj and 'new_city' in obj['fields']:
        obj['fields']['new_city'] = obj['fields']['city']
        del obj['fields']['location']
        del obj['fields']['new_city']

# Yeni temiz JSON dosyasını yaz
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Temizleme tamamlandı. Yeni dosya:", output_file)
