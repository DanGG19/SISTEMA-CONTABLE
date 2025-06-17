from django.contrib import admin
from .models import (
    Empleado,
    CuentaContable, AsientoContable, DetalleAsiento
)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cargo', 'salario_base')

# Registros básicos
admin.site.register(CuentaContable)
admin.site.register(AsientoContable)
admin.site.register(DetalleAsiento)



