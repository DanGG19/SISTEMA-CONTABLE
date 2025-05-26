from django.contrib import admin
from .models import (
    Empleado,
    CuentaContable, AsientoContable, DetalleAsiento,
    Producto, MovimientoInventario
)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cargo', 'salario_base')

# Registros básicos
admin.site.register(CuentaContable)
admin.site.register(AsientoContable)
admin.site.register(DetalleAsiento)

# Configuración avanzada para Producto y MovimientoInventario
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'stock', 'precio_compra')  # precio_venta eliminado

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tipo', 'cantidad', 'precio_unitario', 'iva')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre',)
