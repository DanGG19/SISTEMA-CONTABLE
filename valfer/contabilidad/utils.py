from decimal import Decimal
from django.utils import timezone
from .models import *

def crear_asiento_venta(producto, cantidad, costo_unitario, precio_venta_unitario, porcentaje_iva):
    """
    Registra el asiento contable por la venta de un producto fabricado.
    """
    fecha_hoy = timezone.now().date()

    total_costo = (Decimal(cantidad) * Decimal(costo_unitario)).quantize(Decimal('0.01'))
    total_venta_bruta = (Decimal(cantidad) * Decimal(precio_venta_unitario)).quantize(Decimal('0.01'))
    monto_iva = (total_venta_bruta * Decimal(porcentaje_iva) / Decimal('100')).quantize(Decimal('0.01'))
    total_venta_neta = (total_venta_bruta - monto_iva).quantize(Decimal('0.01'))

    asiento = AsientoContable.objects.create(
        fecha=fecha_hoy,
        descripcion=f"Registro automático de venta de {producto.nombre}"
    )

    cuenta_efectivo = CuentaContable.objects.get(codigo='1101')        # Efectivo
    cuenta_ingreso = CuentaContable.objects.get(codigo='51')           # Ingresos
    cuenta_iva = CuentaContable.objects.get(codigo='2106.01')          # IVA débito fiscal
    cuenta_costo = CuentaContable.objects.get(codigo='4101')           # Costo de venta
    cuenta_inventario = CuentaContable.objects.get(codigo='1105.03')   # Inventario Producto Terminado

    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_efectivo, debe=total_venta_bruta, haber=0)
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_ingreso, debe=0, haber=total_venta_neta)
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_iva, debe=0, haber=monto_iva)
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_costo, debe=total_costo, haber=0)
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_inventario, debe=0, haber=total_costo)


def crear_asiento_kardex_materia_prima(materia, cantidad, precio_unitario_con_iva, porcentaje_iva):
    """
    Crea asiento contable para compra de materia prima con precio unitario que YA incluye IVA.
    """
    fecha_hoy = timezone.now().date()
    total_con_iva = Decimal(cantidad) * Decimal(precio_unitario_con_iva)

    # Precio sin IVA
    base = (total_con_iva / (1 + Decimal(porcentaje_iva) / 100)).quantize(Decimal('0.01'))
    monto_iva = (total_con_iva - base).quantize(Decimal('0.01'))

    asiento = AsientoContable.objects.create(
        fecha=fecha_hoy,
        descripcion=f"Compra de {cantidad} de {materia.nombre} a ${precio_unitario_con_iva} c/u IVA incluido"
    )

    cuenta_inventario = CuentaContable.objects.get(codigo='1105.01')   # Inventario MP
    cuenta_iva = CuentaContable.objects.get(codigo='1104')          # IVA CREDITO FISCAL
    cuenta_efectivo = CuentaContable.objects.get(codigo='1101')        # Efectivo y equivalente

    # Débitos
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_inventario, debe=base, haber=0)
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_iva, debe=monto_iva, haber=0)

    # Crédito
    DetalleAsiento.objects.create(asiento=asiento, fecha=fecha_hoy, cuenta=cuenta_efectivo, debe=0, haber=total_con_iva)

def crear_asiento_ingreso_inventario(producto, cantidad, costo_total):
    """
    Registra un asiento contable que refleja únicamente el ingreso al inventario
    de producto terminado, sin contrapartida (uso específico para control interno).
    """

    fecha_hoy = timezone.now().date()

    asiento = AsientoContable.objects.create(
        fecha=fecha_hoy,
        descripcion=f"Ingreso al inventario por fabricación de {cantidad} unidades de {producto.nombre}"
    )

    cuenta_inventario_pt = CuentaContable.objects.get(codigo='1105.03')  # Inventario Producto Terminado

    DetalleAsiento.objects.create(
        asiento=asiento,
        fecha=fecha_hoy,
        cuenta=cuenta_inventario_pt,
        debe=0,
        haber=Decimal(costo_total)
    )

def registrar_venta_producto_terminado(producto, cantidad, costo_total, precio_unitario_venta, porcentaje_iva):
    """
    Registra los asientos contables correspondientes a la venta de un producto terminado:
    1. Asiento de costo de venta (solo gasto)
    2. Asiento de ingreso con IVA desglosado
    """
    fecha_hoy = timezone.now().date()

    # --- ASIENTO 1: Solo se refleja el costo (no se toca el inventario) ---
    asiento_costo = AsientoContable.objects.create(
        fecha=fecha_hoy,
        descripcion=f"Costo de venta de {cantidad} unidades de {producto.nombre}"
    )

    cuenta_costo_venta = CuentaContable.objects.get(codigo='4101')  # Gasto por costo de ventas

    DetalleAsiento.objects.create(
        asiento=asiento_costo,
        fecha=fecha_hoy,
        cuenta=cuenta_costo_venta,
        debe=Decimal(costo_total),
        haber=0
    )

    # --- ASIENTO 2: Ingreso por venta con IVA desglosado ---
    total_bruto = (Decimal(cantidad) * Decimal(precio_unitario_venta)).quantize(Decimal('0.01'))
    base = (total_bruto / (1 + Decimal(porcentaje_iva) / 100)).quantize(Decimal('0.01'))
    iva = (total_bruto - base).quantize(Decimal('0.01'))

    asiento_venta = AsientoContable.objects.create(
        fecha=fecha_hoy,
        descripcion=f"Venta de {cantidad} unidades de {producto.nombre} a ${precio_unitario_venta} c/u"
    )

    cuenta_efectivo = CuentaContable.objects.get(codigo='1101')   # Caja o Bancos
    cuenta_ingresos = CuentaContable.objects.get(codigo='51')     # Ingresos por ventas
    cuenta_iva = CuentaContable.objects.get(codigo='2106')        # IVA Débito Fiscal

    DetalleAsiento.objects.create(
        asiento=asiento_venta,
        fecha=fecha_hoy,
        cuenta=cuenta_efectivo,
        debe=total_bruto,
        haber=0
    )

    DetalleAsiento.objects.create(
        asiento=asiento_venta,
        fecha=fecha_hoy,
        cuenta=cuenta_ingresos,
        debe=0,
        haber=base
    )

    DetalleAsiento.objects.create(
        asiento=asiento_venta,
        fecha=fecha_hoy,
        cuenta=cuenta_iva,
        debe=0,
        haber=iva
    )