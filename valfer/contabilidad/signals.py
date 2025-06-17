from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import *
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=MovimientoInventario)
def generar_asientos_inventario(sender, instance, created, **kwargs):
    if not created or instance.asiento:
        return  # Evitar duplicados

    producto = instance.producto
    total = instance.cantidad * instance.precio_unitario
    iva_total = total * instance.iva

    # Crear asiento contable
    asiento = AsientoContable.objects.create(
        fecha=instance.fecha,
        descripcion=f"{instance.tipo.capitalize()} de {instance.cantidad} {producto.nombre}"
    )

    # Obtener cuentas (asegúrate de que existan en tu BD)
    cuenta_caja = CuentaContable.objects.get(codigo='1101.01')
    cuenta_iva_credito = CuentaContable.objects.get(codigo='1104.01')
    cuenta_iva_debito = CuentaContable.objects.get(codigo='2106.01')

    if instance.tipo == 'compra':
        # Débito: Inventario
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=producto.cuenta_inventario,
            debe=total,
            haber=0,
            descripcion=f"Compra de {producto.nombre}"
        )
        # Débito: IVA Crédito Fiscal
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=cuenta_iva_credito,
            debe=iva_total,
            haber=0,
            descripcion="IVA Crédito Fiscal"
        )
        # Crédito: Caja
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=cuenta_caja,
            debe=0,
            haber=total + iva_total,
            descripcion="Pago a proveedor"
        )

    elif instance.tipo == 'venta':
        # Débito: Caja
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=cuenta_caja,
            debe=total + iva_total,
            haber=0,
            descripcion="Venta al contado"
        )
        # Crédito: Ingresos por Ventas
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=producto.cuenta_ingresos,
            debe=0,
            haber=total,
            descripcion="Ingreso por venta"
        )
        # Crédito: IVA Débito Fiscal
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=cuenta_iva_debito,
            debe=0,
            haber=iva_total,
            descripcion="IVA Débito Fiscal"
        )
        # Débito: Costo de Venta
        costo_venta = instance.cantidad * producto.precio_compra
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=producto.cuenta_costo_venta,
            debe=costo_venta,
            haber=0,
            descripcion="Costo asociado"
        )
        # Crédito: Inventario
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=instance.fecha,
            cuenta=producto.cuenta_inventario,
            debe=0,
            haber=costo_venta,
            descripcion="Salida de inventario"
        )

    # Vincular el asiento al movimiento
    instance.asiento = asiento
    instance.save()

# Signal para crear empleados automáticamente
@receiver(post_migrate)
def crear_empleados_iniciales(sender, **kwargs):
    """
    Crea empleados predefinidos después de ejecutar las migraciones
    """
    if sender.name == 'contabilidad':
        empleados_iniciales = [
            {
                'nombre': 'María González',
                'dui': '12345678-9',
                'nit': '1234-567890-123-4',
                'cargo': 'Contador',
                'salario_base': 800.00
            },
            {
                'nombre': 'José Rodríguez',
                'dui': '98765432-1',
                'nit': '9876-543210-987-6',
                'cargo': 'Asistente Administrativo',
                'salario_base': 500.00
            },
            {
                'nombre': 'Ana Martínez',
                'dui': '11223344-5',
                'nit': '1122-334455-112-2',
                'cargo': 'Vendedor',
                'salario_base': 450.00
            },
            {
                'nombre': 'Carlos López',
                'dui': '55667788-9',
                'nit': '5566-778899-556-6',
                'cargo': 'Gerente',
                'salario_base': 1200.00
            },
            {
                'nombre': 'Patricia Silva',
                'dui': '33445566-7',
                'nit': '3344-556677-334-4',
                'cargo': 'Secretaria',
                'salario_base': 400.00
            },
            {
                'nombre': 'Roberto Hernández',
                'dui': '77889900-1',
                'nit': '7788-990011-778-8',
                'cargo': 'Operario',
                'salario_base': 365.00
            }
        ]

        for empleado_data in empleados_iniciales:
            empleado, created = Empleado.objects.get_or_create(
                dui=empleado_data['dui'],
                defaults=empleado_data
            )
            if created:
                logger.info(f"Empleado creado: {empleado.nombre}")
            else:
                logger.info(f"Empleado ya existe: {empleado.nombre}")