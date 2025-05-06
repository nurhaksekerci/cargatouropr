from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Sözlükten anahtar ile değer almak için template filtresi.
    Örnek kullanım: {{ my_dict|get_item:key }}
    """
    return dictionary.get(key, []) 

@register.filter
def abs_value(value):
    """
    Negatif sayıyı pozitife çeviren template filtresi.
    Örnek kullanım: {{ negative_number|abs_value }}
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value 