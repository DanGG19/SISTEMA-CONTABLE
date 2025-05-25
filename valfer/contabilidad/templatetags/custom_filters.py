from django import template

register = template.Library()

# Filtro para multiplicar (usado en valor total)
@register.filter(name='mul')
def mul(value, arg):
    """Multiplica dos valores."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0.0

# Filtro para sumar todo el stock
@register.filter(name='sum_stock')
def sum_stock(queryset):
    """Suma el stock de todos los productos."""
    return sum(producto.stock for producto in queryset)

# Filtro para contar productos con stock bajo
@register.filter(name='low_stock_count')
def low_stock_count(queryset, threshold=10):
    """Cuenta productos con stock menor al threshold."""
    return sum(1 for producto in queryset if producto.stock < threshold)

# Filtro para formato monetario
@register.filter(name='currency')
def currency(value):
    """Formatea números como moneda con 2 decimales."""
    return f"${float(value):,.2f}" if value else "$0.00"

@register.filter
def filter_tipo(value, tipo):
    """Filtra por tipo, acepta tanto QuerySet como listas"""
    if hasattr(value, 'filter'):  # Si es QuerySet
        return value.filter(tipo=tipo)
    else:  # Si es lista u otro iterable
        return [item for item in value if item.tipo == tipo]

@register.filter
def currency(value):
    """Formatea como moneda"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"
    
@register.filter
def filter_producto(queryset, producto_id):
    """Filtra por producto_id manteniendo otros filtros"""
    if producto_id and hasattr(queryset, 'filter'):
        return queryset.filter(producto_id=producto_id)
    return queryset

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})