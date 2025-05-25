from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MovimientoInventario, AsientoContable, DetalleAsiento, CuentaContable
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
