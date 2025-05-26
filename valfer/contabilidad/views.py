from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from datetime import datetime
from django.db.models import Sum
from django.utils.timezone import now
from decimal import Decimal
from datetime import date
from calendar import monthrange
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db import transaction

def home(request):
    return render(request, 'contabilidad/home.html')

def catalogo_cuentas(request):
    cuentas = CuentaContable.objects.all().order_by('codigo')

    for cuenta in cuentas:
        cuenta.padding = (cuenta.nivel - 1) * 20

    return render(request, 'contabilidad/catalogo.html', {'cuentas': cuentas})


from django.http import JsonResponse
from .models import AsientoContable

def contar_asientos_por_fecha(request, fecha):
    try:
        fecha_date = datetime.strptime(fecha, "%Y-%m-%d").date()
        count = AsientoContable.objects.filter(fecha=fecha_date).count()
        return JsonResponse({"count": count})
    except ValueError:
        return JsonResponse({"error": "Fecha inválida"}, status=400)


def crear_asiento_contable(request):
    if request.method == 'POST':
        form = AsientoContableForm(request.POST)
        formset = DetalleAsientoFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            fecha = form.cleaned_data.get('fecha') or now().date()
            cantidad = AsientoContable.objects.filter(fecha=fecha).count() + 1
            descripcion = f"{fecha.strftime('%A, %d de %B de %Y')} - Asiento Contable {cantidad}"

            asiento = form.save(commit=False)
            asiento.descripcion = descripcion
            asiento.save()

            detalles = formset.save(commit=False)
            for detalle in detalles:
                detalle.asiento = asiento
                detalle.save()

            messages.success(request, '✅ Asiento contable registrado correctamente.')
            return JsonResponse({'success': True})

        return JsonResponse({'success': False, 'errors': form.errors})

    else:
        form = AsientoContableForm()
        formset = DetalleAsientoFormSet()
        return render(request, 'contabilidad/crear_asiento.html', {
            'form': form,
            'formset': formset,
        })


def listar_asientos(request):
    asientos = AsientoContable.objects.all().order_by('-fecha')
    data = []

    for asiento in asientos:
        total_debe = asiento.detalleasiento_set.aggregate(total=Sum('debe'))['total'] or 0
        total_haber = asiento.detalleasiento_set.aggregate(total=Sum('haber'))['total'] or 0
        data.append({
            'asiento': asiento,
            'total_debe': total_debe,
            'total_haber': total_haber,
        })

    return render(request, 'contabilidad/listar_asientos.html', {
        'asientos_data': data
    })
    
    
def ver_asiento(request, asiento_id):
    asiento = get_object_or_404(AsientoContable, pk=asiento_id)
    detalles = asiento.detalleasiento_set.all()
    return render(request, 'contabilidad/ver_asiento.html', {'asiento': asiento, 'detalles': detalles})

def eliminar_asiento(request, asiento_id):
    if request.method == 'POST':
        try:
            asiento = get_object_or_404(AsientoContable, id=asiento_id)
            asiento.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return HttpResponseNotAllowed(['POST'])


#View para Libro Mayor
def libro_mayor(request):
    anio = int(request.GET.get('anio', date.today().year))
    cuenta_id = request.GET.get('cuenta')

    cuentas = CuentaContable.objects.all().order_by('codigo')
    cuentas_con_saldo = []
    movimientos = []
    saldo_acumulado = 0

    if cuenta_id:
        # Modo Detalle: Mostrar movimientos de la cuenta seleccionada
        cuenta = CuentaContable.objects.get(id=cuenta_id)
        detalles = DetalleAsiento.objects.filter(cuenta=cuenta, fecha__year=anio).order_by('fecha', 'id')

        for detalle in detalles:
            debe = detalle.debe or 0
            haber = detalle.haber or 0
            saldo_acumulado += (debe - haber)
            movimientos.append({
                'fecha': detalle.fecha,
                'descripcion': detalle.asiento.descripcion,
                'debe': debe,
                'haber': haber,
                'saldo_parcial': saldo_acumulado
            })

        return render(request, 'contabilidad/libro_mayor.html', {
            'cuentas': cuentas,
            'cuenta_seleccionada': cuenta,
            'movimientos': movimientos,
            'anio': anio,
            'saldo_final': saldo_acumulado,
        })

    else:
        # Modo Resumen: Mostrar cuentas con saldo ≠ 0
        for cuenta in cuentas:
            detalles = DetalleAsiento.objects.filter(cuenta=cuenta, fecha__year=anio)
            saldo = detalles.aggregate(
                debe=Sum('debe') or 0,
                haber=Sum('haber') or 0
            )
            saldo_final = (saldo['debe'] or 0) - (saldo['haber'] or 0)
            if saldo_final != 0:
                cuentas_con_saldo.append({'cuenta': cuenta, 'saldo': saldo_final})

        return render(request, 'contabilidad/libro_mayor.html', {
            'cuentas': cuentas,
            'cuentas_con_saldo': cuentas_con_saldo,
            'anio': anio,
        })
    

# Crear planilla

def calcular_detalle_planilla(empleado, dias_trabajados):
    salario_diario = empleado.salario_base / Decimal(30)
    salario = salario_diario * Decimal(dias_trabajados)

    # Aportes patronales
    afp_patronal = salario * Decimal('0.0775')
    isss_patronal = salario * Decimal('0.075')

    total_costo_empleador = salario + afp_patronal + isss_patronal

    # Total pagado al empleado = salario (sin descuentos)
    total_pagado = salario

    return salario, afp_patronal, isss_patronal, total_costo_empleador, total_pagado




def crear_planilla(request):
    if request.method == 'POST':
        form = PlanillaForm(request.POST)
        if form.is_valid():
            planilla = form.save()
            return redirect('agregar_detalles', planilla_id=planilla.id)
    else:
        form = PlanillaForm()
    
    return render(request, 'planillas/crear_planilla.html', {'form': form})

def calcular_detalle_planilla(empleado, dias_trabajados):
    salario_diario = empleado.salario_base / Decimal(30)
    salario = salario_diario * Decimal(dias_trabajados)

    afp_patronal = salario * Decimal('0.0775')
    isss_patronal = salario * Decimal('0.075')
    total_costo_empleador = salario + afp_patronal + isss_patronal
    total_pagado = salario  # El empleado recibe el salario sin retenciones

    return salario, afp_patronal, isss_patronal, total_costo_empleador, total_pagado

def agregar_detalles(request, planilla_id):
    planilla = get_object_or_404(Planilla, id=planilla_id)
    empleados = Empleado.objects.all()
    
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado')
        dias = int(request.POST.get('dias_trabajados'))
        empleado = Empleado.objects.get(id=empleado_id)

        salario, afp_patronal, isss_patronal, total_costo_empleador, total_pagado = calcular_detalle_planilla(empleado, dias)

        detalle = DetallePlanilla.objects.create(
            planilla=planilla,
            empleado=empleado,
            dias_trabajados=dias,
            salario=salario,
            afp_patronal=afp_patronal,
            isss_patronal=isss_patronal,
            total_costo_empleador=total_costo_empleador,
            total_pagado=total_pagado
        )

        # 🧾 Crear asiento contable
        try:
            cuenta_salarios = CuentaContable.objects.get(codigo='4103.01.01')  # Salarios
            cuenta_afp = CuentaContable.objects.get(codigo='4103.01.09')  # AFP Patronal
            cuenta_isss = CuentaContable.objects.get(codigo='4103.01.08')  # ISSS Patronal
            cuenta_caja = CuentaContable.objects.get(codigo='1101.01')  # Caja o Bancos
        except CuentaContable.DoesNotExist:
            messages.error(request, "No se encontraron las cuentas contables requeridas.")
            return redirect('agregar_detalles', planilla_id=planilla.id)

        descripcion_asiento = f"Asiento Planilla {planilla.get_mes_display()} {planilla.anio} - {empleado.nombre}"
        asiento = AsientoContable.objects.create(
            fecha=planilla.creada_en.date(),
            descripcion=descripcion_asiento
        )

        # Débito: Salario base
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=planilla.creada_en.date(),
            cuenta=cuenta_salarios,
            debe=salario,
            haber=0,
            descripcion=f"Salario {empleado.nombre}"
        )

        # Débito: AFP Patronal
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=planilla.creada_en.date(),
            cuenta=cuenta_afp,
            debe=afp_patronal,
            haber=0,
            descripcion=f"AFP Patronal {empleado.nombre}"
        )

        # Débito: ISSS Patronal
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=planilla.creada_en.date(),
            cuenta=cuenta_isss,
            debe=isss_patronal,
            haber=0,
            descripcion=f"ISSS Patronal {empleado.nombre}"
        )

        # Crédito: Caja (o Bancos)
        DetalleAsiento.objects.create(
            asiento=asiento,
            fecha=planilla.creada_en.date(),
            cuenta=cuenta_caja,
            debe=0,
            haber=salario + afp_patronal + isss_patronal,
            descripcion=f"Pago planilla {empleado.nombre}"
        )

        messages.success(request, f"Detalle agregado y asiento contable creado para {empleado.nombre}.")
        return redirect('agregar_detalles', planilla_id=planilla.id)

    return render(request, 'planillas/agregar_detalles.html', {
        'planilla': planilla,
        'empleados': empleados
    })

def ver_planilla(request, planilla_id):
    planilla = Planilla.objects.get(id=planilla_id)
    detalles = planilla.detalles.all()

    total_general = sum(d.total_pagado for d in detalles)

    return render(request, 'planillas/ver_planilla.html', {
        'planilla': planilla,
        'detalles': detalles,
        'total_general': total_general,
    })


def listar_planillas(request):
    planillas = Planilla.objects.order_by('-anio', '-mes')  # Ordena por año descendente, luego mes
    return render(request, 'planillas/listar_planillas.html', {'planillas': planillas})

def eliminar_planilla(request, planilla_id):
    planilla = get_object_or_404(Planilla, id=planilla_id)
    planilla.delete()
    messages.success(request, 'Planilla eliminada correctamente.')
    return redirect('listar_planillas')


#Views para el Balance General

def balance_general(request):
    tipo = request.GET.get('tipo', 'mensual')
    anio = int(request.GET.get('anio', date.today().year))
    mes = int(request.GET.get('mes', date.today().month))

    # Definir rango de fechas
    if tipo == 'mensual':
        fecha_inicio = date(anio, mes, 1)
        ultimo_dia = monthrange(anio, mes)[1]
        fecha_fin = date(anio, mes, ultimo_dia)
    elif tipo == 'trimestral':
        trimestre = (mes - 1) // 3 + 1
        mes_inicio = (trimestre - 1) * 3 + 1
        mes_fin = mes_inicio + 2
        fecha_inicio = date(anio, mes_inicio, 1)
        ultimo_dia = monthrange(anio, mes_fin)[1]
        fecha_fin = date(anio, mes_fin, ultimo_dia)
    elif tipo == 'anual':
        fecha_inicio = date(anio, 1, 1)
        fecha_fin = date(anio, 12, 31)
    else:
        fecha_inicio = None
        fecha_fin = None

    detalles = DetalleAsiento.objects.filter(fecha__range=[fecha_inicio, fecha_fin])

    # Calcular saldos por tipo de cuenta (solo si ≠ 0)
    cuentas = CuentaContable.objects.all().order_by('codigo')
    resumen = {'activo': [], 'pasivo': [], 'patrimonio': []}
    totales = {'activo': 0, 'pasivo': 0, 'patrimonio': 0}

    for cuenta in cuentas:
        saldos = detalles.filter(cuenta=cuenta).aggregate(
            debe=Sum('debe') or 0,
            haber=Sum('haber') or 0
        )
        saldo = (saldos['debe'] or 0) - (saldos['haber'] or 0)

        if saldo != 0:
            if cuenta.tipo == 'activo':
                resumen['activo'].append({'cuenta': cuenta, 'saldo': saldo})
                totales['activo'] += saldo
            elif cuenta.tipo == 'pasivo':
                resumen['pasivo'].append({'cuenta': cuenta, 'saldo': -saldo})
                totales['pasivo'] += -saldo
            elif cuenta.tipo == 'patrimonio':
                resumen['patrimonio'].append({'cuenta': cuenta, 'saldo': -saldo})
                totales['patrimonio'] += -saldo

    # Guardar el balance si es POST
    if request.method == 'POST':
        balance = BalanceGeneral.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_activo=totales['activo'],
            total_pasivo=totales['pasivo'],
            total_patrimonio=totales['patrimonio'],
        )

        for tipo in resumen:
            for item in resumen[tipo]:
                DetalleBalance.objects.create(
                    balance=balance,
                    cuenta=item['cuenta'],
                    saldo=item['saldo'],
                )
        return redirect('listar_balances')  # Ajusta la URL según tu proyecto

    return render(request, 'estados/balance_general.html', {
        'resumen': resumen,
        'total_activo': totales['activo'],
        'total_pasivo': totales['pasivo'],
        'total_patrimonio': totales['patrimonio'],
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'anio': anio,
        'tipo': tipo,
        'mes': mes,
    })


def listar_balances(request):
    balances = BalanceGeneral.objects.all().order_by('-fecha_generado')
    return render(request, 'estados/listar_balances.html', {'balances': balances})

#View para estado de resultados
def estado_resultados(request):
    tipos_periodo = [
        ("mensual", "Mensual"),
        ("trimestral", "Trimestral"),
        ("anual", "Anual"),
    ]

    tipo = request.GET.get('tipo', 'mensual')
    anio = int(request.GET.get('anio', date.today().year))
    mes = int(request.GET.get('mes', date.today().month))

    # Calcular rango de fechas
    if tipo == 'mensual':
        fecha_inicio = date(anio, mes, 1)
        ultimo_dia = monthrange(anio, mes)[1]
        fecha_fin = date(anio, mes, ultimo_dia)
    elif tipo == 'trimestral':
        trimestre = (mes - 1) // 3 + 1
        mes_inicio = (trimestre - 1) * 3 + 1
        mes_fin = mes_inicio + 2
        fecha_inicio = date(anio, mes_inicio, 1)
        ultimo_dia = monthrange(anio, mes_fin)[1]
        fecha_fin = date(anio, mes_fin, ultimo_dia)
    elif tipo == 'anual':
        fecha_inicio = date(anio, 1, 1)
        fecha_fin = date(anio, 12, 31)

    detalles = DetalleAsiento.objects.filter(fecha__range=[fecha_inicio, fecha_fin])

    # Calcular ingresos y gastos
    ingresos = []
    gastos = []
    total_ingresos = 0
    total_gastos = 0

    cuentas = CuentaContable.objects.all().order_by('codigo')

    for cuenta in cuentas:
        saldos = detalles.filter(cuenta=cuenta).aggregate(
            debe=Sum('debe') or 0,
            haber=Sum('haber') or 0
        )
        saldo = (saldos['haber'] or 0) - (saldos['debe'] or 0)

        if cuenta.tipo == 'ingreso' and saldo != 0:
            ingresos.append({'cuenta': cuenta, 'saldo': saldo})
            total_ingresos += saldo
        elif cuenta.tipo in ['gasto', 'costo'] and saldo != 0:
            gastos.append({'cuenta': cuenta, 'saldo': saldo})
            total_gastos += saldo

    utilidad = total_ingresos - total_gastos

    # Guardar el estado de resultados
    if request.method == 'POST':
        estado = EstadoResultados.objects.create(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_ingresos=total_ingresos,
            total_gastos=total_gastos,
            utilidad_neta=utilidad,
        )

        for item in ingresos:
            DetalleResultado.objects.create(
                estado=estado,
                cuenta=item['cuenta'],
                monto=item['saldo'],
            )
        for item in gastos:
            DetalleResultado.objects.create(
                estado=estado,
                cuenta=item['cuenta'],
                monto=-item['saldo'],  # Negativo para gastos
            )

        return redirect('listar_resultados')  # Ajusta el nombre según tu ruta

    return render(request, 'estados/estado_resultados.html', {
        'ingresos': ingresos,
        'gastos': gastos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'utilidad': utilidad,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'anio': anio,
        'tipo': tipo,
        'mes': mes,
        'tipos_periodo': tipos_periodo,  # Aquí pasamos la variable al template
    })

def listar_resultados(request):
    resultados = EstadoResultados.objects.all().order_by('-fecha_generado')
    return render(request, 'estados/listar_resultados.html', {'resultados': resultados})

def ver_resultado(request, resultado_id):
    resultado = get_object_or_404(EstadoResultados, pk=resultado_id)
    detalles = resultado.detalles.all().select_related('cuenta').order_by('cuenta__codigo')

    ingresos = []
    gastos = []
    for item in detalles:
        if item.cuenta.tipo == 'ingreso':
            ingresos.append(item)
        else:
            gastos.append(item)

    return render(request, 'estados/ver_resultado.html', {
        'resultado': resultado,
        'ingresos': ingresos,
        'gastos': gastos
    })
#Inventario Perpetuo

def registrar_movimiento(request, tipo):
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.tipo = tipo
            producto = movimiento.producto

            # Validar stock en ventas
            if tipo == 'venta' and producto.stock < movimiento.cantidad:
                form.add_error('cantidad', 'Stock insuficiente')
            else:
                # Actualizar stock según el tipo
                if tipo == 'compra':
                    producto.stock += movimiento.cantidad
                elif tipo == 'venta':
                    producto.stock -= movimiento.cantidad
                producto.save()  # Guardar el nuevo stock

                movimiento.save()  # Guardar el movimiento
                return redirect('lista_inventario')
    else:
        # Si es GET, mostrar el formulario
        initial = {'tipo': tipo, 'iva': 0.13}
        form = MovimientoInventarioForm(initial=initial)

    return render(request, 'inventario/movimiento_form.html', {
        'form': form,
        'titulo': 'Compra' if tipo == 'compra' else 'Venta'
    })



def lista_inventario(request):
    productos = Producto.objects.all()
    movimientos = MovimientoInventario.objects.order_by('-fecha')[:10]  # Últimos 10 movimientos
    return render(request, 'inventario/lista_inventario.html', {
        'productos': productos,
        'movimientos': movimientos
    })

def lista_movimientos(request):
    # Query base SIN filtros para los contadores
    movimientos_base = MovimientoInventario.objects.all()
    
    # Query para la tabla CON filtros
    movimientos_filtrados = movimientos_base.order_by('-fecha')
    
    # Obtener filtros de la request (con valores por defecto seguros)
    producto_id = request.GET.get('producto', '')
    tipo = request.GET.get('tipo', '')
    
    # Aplicar filtros si existen
    if producto_id:
        movimientos_filtrados = movimientos_filtrados.filter(producto_id=producto_id)
    if tipo:
        movimientos_filtrados = movimientos_filtrados.filter(tipo=tipo)
    
    # Calcular totales por movimiento (puede ser útil para la tabla)
    for mov in movimientos_filtrados:
        mov.total_calculado = mov.cantidad * mov.precio_unitario
    
    # Paginación
    paginator = Paginator(movimientos_filtrados, 10)  # 10 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventario/lista_movimientos.html', {
        'movimientos': page_obj,          # Datos paginados y filtrados
        'movimientos_base': movimientos_base,  # Datos SIN filtrar para contadores
        'productos': Producto.objects.all(),
        'page_obj': page_obj,
        # Filtros para mantener selección en la UI
        'producto_seleccionado': producto_id,
        'tipo_seleccionado': tipo
    })


def seleccionar_movimiento(request):
    productos = Producto.objects.all()
    return render(request, 'inventario/seleccionar_movimiento.html', {'productos': productos})


#Calcular el IVA

def calcular_iva(request):
    MES_NOMBRES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
        (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
        (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    anio = int(request.GET.get('anio', date.today().year))
    mes = int(request.GET.get('mes', date.today().month))

    fecha_inicio = date(anio, mes, 1)
    ultimo_dia = monthrange(anio, mes)[1]
    fecha_fin = date(anio, mes, ultimo_dia)

    detalles = DetalleAsiento.objects.filter(fecha__range=[fecha_inicio, fecha_fin])

    # Cuentas de IVA (ajusta los prefijos si es necesario)
    cuentas_credito = CuentaContable.objects.filter(codigo__startswith='1104')
    cuentas_debito = CuentaContable.objects.filter(codigo__startswith='2106')

    total_credito = 0
    total_debito = 0

    for cuenta in cuentas_credito:
        saldo = detalles.filter(cuenta=cuenta).aggregate(
            debe=Sum('debe') or 0,
            haber=Sum('haber') or 0
        )
        total_credito += (saldo['debe'] or 0) - (saldo['haber'] or 0)

    for cuenta in cuentas_debito:
        saldo = detalles.filter(cuenta=cuenta).aggregate(
            debe=Sum('debe') or 0,
            haber=Sum('haber') or 0
        )
        total_debito += (saldo['haber'] or 0) - (saldo['debe'] or 0)

    iva_pagar = total_debito - total_credito

    if request.method == 'POST':
        asiento = AsientoContable.objects.create(
            fecha=fecha_fin,
            descripcion=f"Cierre de IVA - {fecha_inicio.strftime('%B %Y')}"
        )

        for cuenta in cuentas_debito:
            saldo = detalles.filter(cuenta=cuenta).aggregate(
                debe=Sum('debe') or 0,
                haber=Sum('haber') or 0
            )
            saldo_debito = (saldo['haber'] or 0) - (saldo['debe'] or 0)
            if saldo_debito != 0:
                DetalleAsiento.objects.create(
                    asiento=asiento,
                    fecha=fecha_fin,
                    cuenta=cuenta,
                    debe=saldo_debito,
                    haber=0
                )

        for cuenta in cuentas_credito:
            saldo = detalles.filter(cuenta=cuenta).aggregate(
                debe=Sum('debe') or 0,
                haber=Sum('haber') or 0
            )
            saldo_credito = (saldo['debe'] or 0) - (saldo['haber'] or 0)
            if saldo_credito != 0:
                DetalleAsiento.objects.create(
                    asiento=asiento,
                    fecha=fecha_fin,
                    cuenta=cuenta,
                    debe=0,
                    haber=saldo_credito
                )

        cuenta_iva_pagar = CuentaContable.objects.get(codigo='2102.03')
        if iva_pagar > 0:
            DetalleAsiento.objects.create(
                asiento=asiento,
                fecha=fecha_fin,
                cuenta=cuenta_iva_pagar,
                debe=0,
                haber=iva_pagar
            )
        elif iva_pagar < 0:
            DetalleAsiento.objects.create(
                asiento=asiento,
                fecha=fecha_fin,
                cuenta=cuenta_iva_pagar,
                debe=abs(iva_pagar),
                haber=0
            )

        return redirect('listar_asientos')

    return render(request, 'contabilidad/calcular_iva.html', {
        'anio': anio,
        'mes': mes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_debito': total_debito,
        'total_credito': total_credito,
        'iva_pagar': iva_pagar,
        'meses': MES_NOMBRES,
    })


#view para ajustes contables
def crear_ajuste(request):
    cuentas = CuentaContable.objects.all().order_by('codigo')

    if request.method == 'POST':
        fecha = request.POST.get('fecha') or timezone.now().date()
        descripcion = request.POST.get('descripcion', 'Ajuste Contable Manual')

        asiento = AsientoContable.objects.create(
            fecha=fecha,
            descripcion=descripcion
        )

        for cuenta_id in request.POST.getlist('cuenta_id'):
            debe = float(request.POST.get(f'debe_{cuenta_id}', 0) or 0)
            haber = float(request.POST.get(f'haber_{cuenta_id}', 0) or 0)

            if debe != 0 or haber != 0:
                cuenta = CuentaContable.objects.get(id=cuenta_id)
                DetalleAsiento.objects.create(
                    asiento=asiento,
                    fecha=fecha,
                    cuenta=cuenta,
                    debe=debe,
                    haber=haber
                )

        return redirect('listar_asientos')  # Cambia por la ruta de tu listado de asientos

    return render(request, 'contabilidad/crear_ajuste.html', {
        'cuentas': cuentas
    })


def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            
            # Asignar cuentas automáticamente
            try:
                producto.cuenta_inventario = CuentaContable.objects.get(codigo='1105.01')  # Inventario de materia prima
                producto.cuenta_costo_venta = CuentaContable.objects.get(codigo='4101.01')  # Inventarios
                producto.cuenta_ingresos = CuentaContable.objects.get(codigo='5101.01')  # Ventas a consumidor final
            except CuentaContable.DoesNotExist:
                form.add_error(None, 'No se encontraron las cuentas contables requeridas en el catálogo.')
                return render(request, 'inventario/agregar_producto.html', {'form': form, 'titulo': 'Agregar Producto'})
            
            producto.save()
            return redirect('seleccionar_movimiento')
    else:
        form = ProductoForm()
    
    return render(request, 'inventario/agregar_producto.html', {'form': form, 'titulo': 'Agregar Producto'})


#Vista para eliminar un movimiento de inventario 
@transaction.atomic
def eliminar_movimiento(request, pk):
    movimiento = get_object_or_404(MovimientoInventario, pk=pk)

    if request.method == 'POST':
        producto = movimiento.producto

        # Revertir stock
        if movimiento.tipo == 'compra':
            producto.stock -= movimiento.cantidad
        elif movimiento.tipo == 'venta':
            producto.stock += movimiento.cantidad
        producto.save()

        # Eliminar asiento contable si existe
        if movimiento.asiento:
            movimiento.asiento.delete()

        # Eliminar movimiento
        movimiento.delete()

        return redirect('lista_movimientos')

    return render(request, 'inventario/eliminar_movimiento.html', {'movimiento': movimiento})


#Crud para productos
def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'inventario/lista_productos.html', {'productos': productos, 'titulo': 'Lista de Productos'})

def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.cuenta_inventario = CuentaContable.objects.get(codigo='1102.01')
            producto.cuenta_costo_venta = CuentaContable.objects.get(codigo='4101.01')
            producto.cuenta_ingresos = CuentaContable.objects.get(codigo='5101.01')
            producto.save()
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventario/agregar_producto.html', {'form': form, 'titulo': 'Editar Producto'})

def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return redirect('lista_productos')
    return render(request, 'inventario/eliminar_producto.html', {'producto': producto})


#View para cierre contable
def cierre_contable(request):
    anio = int(request.GET.get('anio', date.today().year))
    fecha_cierre = date(anio, 12, 31)

    detalles = DetalleAsiento.objects.filter(fecha__year=anio)
    cuentas_ingresos = CuentaContable.objects.filter(tipo='ingreso')
    cuentas_gastos = CuentaContable.objects.filter(tipo__in=['gasto', 'costo'])

    total_ingresos = 0
    total_gastos = 0

    for cuenta in cuentas_ingresos:
        saldo = detalles.filter(cuenta=cuenta).aggregate(
            debe=Sum('debe') or 0,
            haber=Sum('haber') or 0
        )
        total_ingresos += (saldo['haber'] or 0) - (saldo['debe'] or 0)

    for cuenta in cuentas_gastos:
        saldo = detalles.filter(cuenta=cuenta).aggregate(
            debe=Sum('debe') or 0,
            haber=Sum('haber') or 0
        )
        total_gastos += (saldo['debe'] or 0) - (saldo['haber'] or 0)

    resultado_ejercicio = total_ingresos - total_gastos

    if request.method == 'POST':
        asiento = AsientoContable.objects.create(
            fecha=fecha_cierre,
            descripcion=f"Cierre Contable del Ejercicio {anio}"
        )

        cuenta_pyg = CuentaContable.objects.get(codigo='6101.01')  # Pérdidas y Ganancias
        cuenta_utilidad = CuentaContable.objects.get(codigo='310401')  # Utilidad del Ejercicio
        cuenta_perdida = CuentaContable.objects.get(codigo='310402')  # Pérdida del Ejercicio

        # Cerrar Ingresos → PYG
        for cuenta in cuentas_ingresos:
            saldo = detalles.filter(cuenta=cuenta).aggregate(
                debe=Sum('debe') or 0,
                haber=Sum('haber') or 0
            )
            saldo_ingreso = (saldo['haber'] or 0) - (saldo['debe'] or 0)
            if saldo_ingreso != 0:
                DetalleAsiento.objects.create(
                    asiento=asiento,
                    fecha=fecha_cierre,
                    cuenta=cuenta,
                    debe=saldo_ingreso,
                    haber=0
                )
                DetalleAsiento.objects.create(
                    asiento=asiento,
                    fecha=fecha_cierre,
                    cuenta=cuenta_pyg,
                    debe=0,
                    haber=saldo_ingreso
                )

        # Cerrar Gastos → PYG
        for cuenta in cuentas_gastos:
            saldo = detalles.filter(cuenta=cuenta).aggregate(
                debe=Sum('debe') or 0,
                haber=Sum('haber') or 0
            )
            saldo_gasto = (saldo['debe'] or 0) - (saldo['haber'] or 0)
            if saldo_gasto != 0:
                DetalleAsiento.objects.create(
                    asiento=asiento,
                    fecha=fecha_cierre,
                    cuenta=cuenta_pyg,
                    debe=saldo_gasto,
                    haber=0
                )
                DetalleAsiento.objects.create(
                    asiento=asiento,
                    fecha=fecha_cierre,
                    cuenta=cuenta,
                    debe=0,
                    haber=saldo_gasto
                )

        # Trasladar saldo de PYG a Utilidad/Pérdida
        if resultado_ejercicio > 0:
            DetalleAsiento.objects.create(
                asiento=asiento,
                fecha=fecha_cierre,
                cuenta=cuenta_pyg,
                debe=resultado_ejercicio,
                haber=0
            )
            DetalleAsiento.objects.create(
                asiento=asiento,
                fecha=fecha_cierre,
                cuenta=cuenta_utilidad,
                debe=0,
                haber=resultado_ejercicio
            )
        elif resultado_ejercicio < 0:
            DetalleAsiento.objects.create(
                asiento=asiento,
                fecha=fecha_cierre,
                cuenta=cuenta_perdida,
                debe=abs(resultado_ejercicio),
                haber=0
            )
            DetalleAsiento.objects.create(
                asiento=asiento,
                fecha=fecha_cierre,
                cuenta=cuenta_pyg,
                debe=0,
                haber=abs(resultado_ejercicio)
            )

        messages.success(request, f"✅ Cierre Contable del Ejercicio {anio} realizado correctamente. Todas las cuentas de resultados han sido cerradas.")
        return redirect('listar_asientos')

    return render(request, 'contabilidad/cierre_contable.html', {
        'anio': anio,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'utilidad': resultado_ejercicio,
    })