from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import AsientoContableForm, DetalleAsientoFormSet, PlanillaForm, MovimientoInventarioForm
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

# Crear planilla

def calcular_detalle_planilla(empleado, dias_trabajados):
    salario_diario = empleado.salario_base / Decimal(30)
    salario = salario_diario * Decimal(dias_trabajados)
    afp = salario * Decimal('0.0725')  # 7.25%
    renta = salario * Decimal('0.10')  # 10%
    total_pagado = salario - afp - renta
    return salario, afp, renta, total_pagado


def crear_planilla(request):
    if request.method == 'POST':
        form = PlanillaForm(request.POST)
        if form.is_valid():
            planilla = form.save()
            return redirect('agregar_detalles', planilla_id=planilla.id)
    else:
        form = PlanillaForm()
    return render(request, 'contabilidad/crear_planilla.html', {'form': form})


def agregar_detalles(request, planilla_id):
    planilla = Planilla.objects.get(id=planilla_id)
    empleados = Empleado.objects.all()
    
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado')
        dias = int(request.POST.get('dias_trabajados'))
        empleado = Empleado.objects.get(id=empleado_id)

        salario, afp, renta, total = calcular_detalle_planilla(empleado, dias)

        DetallePlanilla.objects.create(
            planilla=planilla,
            empleado=empleado,
            dias_trabajados=dias,
            salario=salario,
            afp=afp,
            renta=renta,
            total_pagado=total
        )
        messages.success(request, 'Detalle agregado')
        return redirect('agregar_detalles', planilla_id=planilla.id)

    return render(request, 'contabilidad/agregar_detalles.html', {
        'planilla': planilla,
        'empleados': empleados
    })

def ver_planilla(request, planilla_id):
    planilla = Planilla.objects.get(id=planilla_id)
    detalles = planilla.detalles.all()

    total_general = sum(d.total_pagado for d in detalles)

    return render(request, 'contabilidad/ver_planilla.html', {
        'planilla': planilla,
        'detalles': detalles,
        'total_general': total_general,
    })

from django.shortcuts import render
from .models import Planilla

def listar_planillas(request):
    planillas = Planilla.objects.order_by('-anio', '-mes')  # ✅ Ordena por año descendente, luego mes
    return render(request, 'contabilidad/listar_planillas.html', {'planillas': planillas})

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
