from decimal import Decimal
from django.utils import timezone
from .models import AsientoContable, DetalleAsiento, CuentaContable

def crear_asiento_venta(producto, cantidad, costo_unitario, precio_venta_unitario, porcentaje_iva):
    """
    Registra el asiento contable por la venta de un producto fabricado.
    """
    fecha_hoy = timezone.now().date()
    
    total_costo = Decimal(cantidad) * Decimal(costo_unitario)
    total_venta_bruta = Decimal(cantidad) * Decimal(precio_venta_unitario)
    monto_iva = (total_venta_bruta * Decimal(porcentaje_iva) / Decimal('100')).quantize(Decimal('0.01'))
    total_venta_neta = (total_venta_bruta - monto_iva).quantize(Decimal('0.01'))

    asiento = AsientoContable.objects.create(
        fecha=fecha_hoy,
        descripcion=f"Registro automático venta de {producto.nombre}"
    )

    # Débito: Cliente (suponiendo venta al contado, usaríamos efectivo)
    cuenta_efectivo = CuentaContable.objects.get(codigo='1101')
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_efectivo, debe=total_venta_bruta, haber=0)

    # Crédito: Ingreso por ventas
    cuenta_ingreso = CuentaContable.objects.get(codigo='51')
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_ingreso, debe=0, haber=total_venta_neta)

    # Crédito: IVA débito fiscal
    cuenta_iva = CuentaContable.objects.get(codigo='2106.01')
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_iva, debe=0, haber=monto_iva)

    # Débito: Costo de Venta
    cuenta_costo = CuentaContable.objects.get(codigo='4101')
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_costo, debe=total_costo, haber=0)

    # Crédito: Inventario Producto Terminado
    cuenta_inventario = CuentaContable.objects.get(codigo='1105.03')
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_inventario, debe=0, haber=total_costo)
