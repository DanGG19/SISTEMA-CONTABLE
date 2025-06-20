from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from datetime import datetime
from django.db.models import Sum, Q
from django.utils.timezone import now
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import date
from calendar import monthrange
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db import transaction
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .utils import crear_asiento_venta


def home(request):
    return render(request, 'contabilidad/home.html')

def catalogo_cuentas(request):
    cuentas = CuentaContable.objects.all().order_by('codigo')

    for cuenta in cuentas:
        cuenta.padding = (cuenta.nivel - 1) * 20

    return render(request, 'contabilidad/catalogo.html', {'cuentas': cuentas})

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
            afp=afp_patronal,
            isss=isss_patronal,
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


#ViewS PARA hora de trabajo
def hoja_trabajo(request):
    # Filtros de periodo
    periodo_inicio = request.GET.get('inicio')
    periodo_fin = request.GET.get('fin')
    filtro_fecha = Q()
    if periodo_inicio and periodo_fin:
        filtro_fecha = Q(fecha__range=[periodo_inicio, periodo_fin])

    # --- Formulario de ajuste manual ---
    cuentas = CuentaContable.objects.all().order_by('codigo')
    if request.method == 'POST':
        cuenta_id = request.POST.get('cuenta')
        debe = float(request.POST.get('debe', 0) or 0)
        haber = float(request.POST.get('haber', 0) or 0)
        descripcion = request.POST.get('descripcion', 'ajuste manual').strip() or 'ajuste manual'

        if cuenta_id and (debe > 0 or haber > 0):
            cuenta = CuentaContable.objects.get(id=cuenta_id)
            # Crea un asiento para el ajuste manual
            asiento = AsientoContable.objects.create(
                fecha=timezone.now().date(),
                descripcion=descripcion
            )
            DetalleAsiento.objects.create(
                asiento=asiento,
                fecha=asiento.fecha,
                descripcion=descripcion,
                cuenta=cuenta,
                debe=debe,
                haber=haber
            )
        return redirect('hoja_trabajo')  # Cambia por el name de tu urlpattern

    # --- Calcular movimientos por cuenta ---
    datos = []
    for cuenta in cuentas:
        debe = DetalleAsiento.objects.filter(cuenta=cuenta).filter(filtro_fecha).aggregate(Sum('debe'))['debe__sum'] or 0
        haber = DetalleAsiento.objects.filter(cuenta=cuenta).filter(filtro_fecha).aggregate(Sum('haber'))['haber__sum'] or 0

        ajuste_debe = DetalleAsiento.objects.filter(
            cuenta=cuenta,
            asiento__descripcion__icontains='ajuste'
        ).filter(filtro_fecha).aggregate(Sum('debe'))['debe__sum'] or 0

        ajuste_haber = DetalleAsiento.objects.filter(
            cuenta=cuenta,
            asiento__descripcion__icontains='ajuste'
        ).filter(filtro_fecha).aggregate(Sum('haber'))['haber__sum'] or 0

        ajustado_debe = debe + ajuste_debe
        ajustado_haber = haber + ajuste_haber

        datos.append({
            'cuenta': cuenta,
            'debe': debe,
            'haber': haber,
            'ajuste_debe': ajuste_debe,
            'ajuste_haber': ajuste_haber,
            'ajustado_debe': ajustado_debe,
            'ajustado_haber': ajustado_haber,
            'tipo': cuenta.tipo,
        })

    # Mostrar solo cuentas con movimiento distinto de cero
    datos = [
        x for x in datos
        if x['debe'] or x['haber'] or x['ajuste_debe'] or x['ajuste_haber'] or x['ajustado_debe'] or x['ajustado_haber']
    ]

    total_debe = sum(x['debe'] for x in datos)
    total_haber = sum(x['haber'] for x in datos)
    total_ajuste_debe = sum(x['ajuste_debe'] for x in datos)
    total_ajuste_haber = sum(x['ajuste_haber'] for x in datos)
    total_ajustado_debe = sum(x['ajustado_debe'] for x in datos)
    total_ajustado_haber = sum(x['ajustado_haber'] for x in datos)

    context = {
        'datos': datos,
        'cuentas': cuentas,
        'total_debe': total_debe,
        'total_haber': total_haber,
        'total_ajuste_debe': total_ajuste_debe,
        'total_ajuste_haber': total_ajuste_haber,
        'total_ajustado_debe': total_ajustado_debe,
        'total_ajustado_haber': total_ajustado_haber,
    }
    return render(request, 'estados/hoja_trabajo.html', context)



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')  
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'login/login.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')



# VISTAS KARDEX METODO PEPS

def kardex_home(request):
    return render(request, 'inventario/kardex_home.html')

def kardex_materia_prima_list(request, materia_prima_id):
    materia = get_object_or_404(MateriaPrima, id=materia_prima_id)
    movimientos = KardexMateriaPrima.objects.filter(materia_prima=materia).order_by('fecha', 'id')
    existencias_peps = calcular_existencias_peps(movimientos)
    movimientos_y_lotes = zip(movimientos, existencias_peps)
    return render(request, 'inventario/kardex_materia_prima_list.html', {
        'materia': materia,
        'movimientos_y_lotes': movimientos_y_lotes,
    })



def kardex_materia_prima_nuevo(request, materia_prima_id):
    materia = get_object_or_404(MateriaPrima, id=materia_prima_id)
    if request.method == 'POST':
        form = KardexMateriaPrimaForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.materia_prima = materia
            # Calcular el total del movimiento antes de guardar
            movimiento.total = movimiento.cantidad * movimiento.costo_unitario

            # Obtener el último movimiento registrado para la materia prima
            ultimo = KardexMateriaPrima.objects.filter(materia_prima=materia).order_by('-fecha', '-id').first()

            # Primer movimiento (solo entrada válida)
            if not ultimo:
                if movimiento.tipo_movimiento == 'entrada':
                    movimiento.saldo_cantidad = movimiento.cantidad
                    movimiento.saldo_total = movimiento.total
                else:
                    messages.error(request, "Primero debe registrar una entrada para esta materia prima.")
                    return redirect('kardex_materia_prima_nuevo', materia_prima_id=materia.id)
            else:
                if movimiento.tipo_movimiento == 'entrada':
                    movimiento.saldo_cantidad = ultimo.saldo_cantidad + movimiento.cantidad
                    movimiento.saldo_total = ultimo.saldo_total + movimiento.total
                elif movimiento.tipo_movimiento in ['salida', 'proceso']:
                    if movimiento.cantidad > ultimo.saldo_cantidad:
                        messages.error(request, "No hay suficiente saldo para esta salida.")
                        return redirect('kardex_materia_prima_nuevo', materia_prima_id=materia.id)
                    movimiento.saldo_cantidad = ultimo.saldo_cantidad - movimiento.cantidad
                    # (NOTA: Esto usa el último costo_unitario, no PEPS real)
                    movimiento.saldo_total = ultimo.saldo_total - (movimiento.cantidad * ultimo.costo_unitario)
                else:
                    # En caso de nuevos tipos de movimientos
                    movimiento.saldo_cantidad = ultimo.saldo_cantidad
                    movimiento.saldo_total = ultimo.saldo_total

            movimiento.save()
            messages.success(request, "Movimiento registrado exitosamente.")
            return redirect('kardex_materia_prima_list', materia_prima_id=materia.id)
    else:
        form = KardexMateriaPrimaForm()
    return render(request, 'inventario/kardex_materia_prima_nuevo.html', {
        'materia': materia,
        'form': form,
    })

def calcular_existencias_peps(movimientos):
    lotes = []
    estado_por_movimiento = []

    for mov in movimientos:
        if mov.tipo_movimiento == 'entrada':
            lotes.append({
                'cantidad': float(mov.cantidad),
                'costo_unitario': float(mov.costo_unitario),
            })
        elif mov.tipo_movimiento in ['salida', 'proceso']:
            cantidad_restante = float(mov.cantidad)
            while cantidad_restante > 0 and lotes:
                lote = lotes[0]
                if lote['cantidad'] > cantidad_restante:
                    lote['cantidad'] -= cantidad_restante
                    cantidad_restante = 0
                else:
                    cantidad_restante -= lote['cantidad']
                    lotes.pop(0)

        # String tipo "(4x250)+(2x200)"
        detalle = "+".join(
            f"({int(l['cantidad'])}*{int(l['costo_unitario'])})" for l in lotes if l['cantidad'] > 0
        ) if lotes else "0"

        unidades_totales = sum(l['cantidad'] for l in lotes)
        valor_total = sum(l['cantidad'] * l['costo_unitario'] for l in lotes)

        estado_por_movimiento.append({
            "detalle": detalle,
            "unidades_totales": unidades_totales,
            "valor_total": valor_total,
        })
    return estado_por_movimiento


#Views para lista de Kardex de Producto Terminado
def listar_kardex_productos_terminados(request):
    productos = ProductoTerminado.objects.all()
    return render(request, 'fabricacion/lista_productos_terminados.html', {
        'productos': productos,
    })


def kardex_producto_terminado(request, producto_id):
    producto = get_object_or_404(ProductoTerminado, id=producto_id)
    movimientos = KardexProductoTerminado.objects.filter(
        producto=producto
    ).order_by('fecha', 'id')
    
    movimientos_y_lotes = []
    lotes_actuales = []
    total_existencias = Decimal('0')
    total_valor = Decimal('0')
    
    for mov in movimientos:
        if mov.tipo_movimiento == 'ingreso':
            lotes_actuales.append({'cantidad': mov.cantidad, 'costo_unitario': mov.costo_unitario})
            total_existencias += mov.cantidad
            total_valor += mov.cantidad * mov.costo_unitario
        elif mov.tipo_movimiento == 'salida':
            cantidad_a_sacar = mov.cantidad
            valor_salida = Decimal('0')
            detalle_lotes = []
            i = 0
            while cantidad_a_sacar > 0 and i < len(lotes_actuales):
                lote = lotes_actuales[i]
                consumir = min(lote['cantidad'], cantidad_a_sacar)
                valor_salida += consumir * lote['costo_unitario']
                detalle_lotes.append(f"{consumir}x{lote['costo_unitario']}")
                lote['cantidad'] -= consumir
                cantidad_a_sacar -= consumir
                if lote['cantidad'] == 0:
                    i += 1
            lotes_actuales = [l for l in lotes_actuales if l['cantidad'] > 0]
            total_existencias -= mov.cantidad
            total_valor -= valor_salida
        detalle_existencias = " + ".join(
            [f"({l['cantidad']}*{l['costo_unitario']})" for l in lotes_actuales]
        ) if lotes_actuales else ""
        movimientos_y_lotes.append((
            mov,
            {
                'unidades_totales': total_existencias,
                'detalle': detalle_existencias,
                'valor_total': total_valor,
            }
        ))

    # -------- Lógica para el botón de fabricación --------
    # Puedes cambiar los nombres exactos según tu base de datos y signals
    nombre = producto.nombre.lower()
    if "bolsa" in nombre:
        fabricar_url = 'fabricar_embolsar_cafe'
        texto_boton = 'Fabricar Bolsas de Café'
    elif "mezcla" in nombre:
        fabricar_url = 'fabricar_mezcla_licor'
        texto_boton = 'Fabricar Mezcla de Licor de Café'
    elif "licor" in nombre or "750ml" in nombre:
        fabricar_url = 'fabricar_embotellar_licor'
        texto_boton = 'Fabricar Licor de Café 750ml'
    else:
        fabricar_url = None
        texto_boton = None

    return render(request, 'fabricacion/kardex_producto_terminado.html', {
        'producto': producto,
        'movimientos_y_lotes': movimientos_y_lotes,
        'fabricar_url': fabricar_url,
        'texto_boton': texto_boton,
    })

def fabricar_embolsar_cafe(request):
    if request.method == 'POST':
        try:
            bolsas_a_fabricar = int(request.POST['cantidad_bolsas'])
            mano_obra_por_hora = Decimal(request.POST['mano_obra_por_hora'])
            horas_trabajadas = Decimal(request.POST['horas_trabajadas'])
        except (KeyError, ValueError, InvalidOperation):
            messages.error(request, "Por favor ingresa valores válidos en todos los campos.")
            return redirect('fabricar_embolsar_cafe')

        # Validaciones básicas
        if bolsas_a_fabricar <= 0:
            messages.error(request, "La cantidad de bolsas debe ser mayor a cero.")
            return redirect('fabricar_embolsar_cafe')
        if mano_obra_por_hora < 0 or horas_trabajadas < 0:
            messages.error(request, "El costo por hora y las horas trabajadas no pueden ser negativos.")
            return redirect('fabricar_embolsar_cafe')

        # Calcular materia prima necesaria
        gramos_necesarios = Decimal(bolsas_a_fabricar) * Decimal('400')
        quintales_necesarios = (gramos_necesarios / Decimal('100000')).quantize(Decimal('0.0001'))

        materia_prima = get_object_or_404(MateriaPrima, nombre__iexact="Café en Quintales")
        movimientos = KardexMateriaPrima.objects.filter(
            materia_prima=materia_prima
        ).order_by('fecha', 'id')

        cantidad_restante = quintales_necesarios
        costo_total_mp = Decimal('0')
        consumido_lotes = []

        for mov in movimientos:
            if mov.saldo_cantidad > 0 and cantidad_restante > 0:
                a_consumir = min(mov.saldo_cantidad, cantidad_restante)
                costo_total_mp += a_consumir * mov.costo_unitario
                consumido_lotes.append({
                    "lote_id": mov.id,
                    "cantidad": a_consumir,
                    "costo_unitario": mov.costo_unitario,
                    "total": (a_consumir * mov.costo_unitario).quantize(Decimal('0.01')),
                })
                # Registrar salida en KardexMateriaPrima por lote consumido
                nueva_saldo_cantidad = mov.saldo_cantidad - a_consumir
                nueva_saldo_total = mov.saldo_total - (a_consumir * mov.costo_unitario)
                KardexMateriaPrima.objects.create(
                    materia_prima=materia_prima,
                    fecha=timezone.now(),
                    tipo_movimiento='salida',
                    concepto=f"Consumo para fabricación de bolsas",
                    cantidad=a_consumir,
                    costo_unitario=mov.costo_unitario,
                    total=(a_consumir * mov.costo_unitario),
                    saldo_cantidad=nueva_saldo_cantidad,
                    saldo_total=nueva_saldo_total,
                )
                # Actualizar el saldo del movimiento original
                mov.saldo_cantidad = nueva_saldo_cantidad
                mov.saldo_total = nueva_saldo_total
                mov.save()
                cantidad_restante -= a_consumir
            if cantidad_restante <= 0:
                break

        if cantidad_restante > 0:
            messages.error(request, "No hay suficiente café en inventario para fabricar esa cantidad de bolsas.")
            return redirect('fabricar_embolsar_cafe')

        # Cálculo de mano de obra y CIF
        costo_mano_obra = (mano_obra_por_hora * horas_trabajadas).quantize(Decimal('0.01'))
        cif = ((costo_total_mp + costo_mano_obra) * Decimal('0.30')).quantize(Decimal('0.01'))
        costo_total = (costo_total_mp + costo_mano_obra + cif).quantize(Decimal('0.01'))

        producto_final = get_object_or_404(ProductoTerminado, nombre__iexact="Bolsa Café 400g")
        proceso = ProcesoFabricacion.objects.create(
            tipo='embolsar_cafe',
            producto_final=producto_final,
            cantidad_producida=bolsas_a_fabricar,
            gramos_usados=gramos_necesarios,
            quintales_usados=quintales_necesarios,
            costo_materia_prima=costo_total_mp,
            costo_mano_obra=costo_mano_obra,
            cif=cif,
            costo_total=costo_total
        )

        # Kardex de producto terminado (entrada)
        ultimo_kardex = KardexProductoTerminado.objects.filter(
            producto=producto_final
        ).order_by('-fecha', '-id').first()
        saldo_cantidad = (ultimo_kardex.saldo_cantidad if ultimo_kardex else Decimal('0')) + Decimal(bolsas_a_fabricar)
        saldo_total = (ultimo_kardex.saldo_total if ultimo_kardex else Decimal('0')) + costo_total

        KardexProductoTerminado.objects.create(
            producto=producto_final,
            fecha=timezone.now(),
            tipo_movimiento='ingreso',
            concepto=f"Fabricación por proceso {proceso.id}",
            cantidad=Decimal(bolsas_a_fabricar),
            costo_unitario=(costo_total / Decimal(bolsas_a_fabricar)).quantize(Decimal('0.01')),
            total=costo_total,
            saldo_cantidad=saldo_cantidad,
            saldo_total=saldo_total,
        )

        messages.success(request, f"Fabricación registrada exitosamente. Costo total: ${costo_total:,.2f}")
    
        crear_asiento_venta(
            producto_final, 
            cantidad=bolsas_a_fabricar,
            costo_unitario=(costo_total / Decimal(bolsas_a_fabricar)).quantize(Decimal('0.01')),
            precio_venta_unitario=Decimal('3.50'),
            porcentaje_iva=Decimal('13')
        )
        return render(request, 'fabricacion/fabricar_embolsar_cafe_exito.html', {
            'proceso': proceso,
            'consumido_lotes': consumido_lotes,
        })

    return render(request, 'fabricacion/fabricar_embolsar_cafe.html')


#view para fabricar licor
def fabricar_mezcla_licor(request):
    if request.method == 'POST':
        try:
            litros_a_fabricar = Decimal(request.POST['cantidad_litros'])
            mano_obra_por_hora = Decimal(request.POST['mano_obra_por_hora'])
            horas_trabajadas = Decimal(request.POST['horas_trabajadas'])
        except (KeyError, ValueError, InvalidOperation):
            messages.error(request, "Por favor ingresa valores válidos en todos los campos.")
            return redirect('fabricar_mezcla_licor')

        if litros_a_fabricar <= 0:
            messages.error(request, "La cantidad a fabricar debe ser mayor a cero.")
            return redirect('fabricar_mezcla_licor')

        if mano_obra_por_hora < 0 or horas_trabajadas < 0:
            messages.error(request, "El costo por hora y las horas trabajadas no pueden ser negativos.")
            return redirect('fabricar_mezcla_licor')

        # 1. Cálculo de insumos requeridos (ajustar a tu lógica)
        # Por cada 400 litros: 1 quintal café, 10 litros alcohol, 15 garrafones de agua (300 litros)
        proporcion = litros_a_fabricar / Decimal('400')
        quintales_cafe = proporcion * Decimal('1')
        litros_licor = proporcion * Decimal('10')
        garrafones_agua = (proporcion * Decimal('15')).quantize(Decimal('0.0001'))
        litros_agua = garrafones_agua * Decimal('20')

        # 2. Materias primas
        mp_cafe = get_object_or_404(MateriaPrima, nombre__iexact="Café en Quintales")
        mp_licor = get_object_or_404(MateriaPrima, nombre__iexact="Botella de licor")
        mp_agua = get_object_or_404(MateriaPrima, nombre__iexact="Garrafón de agua")

        # --- Consumo de Café
        movimientos_cafe = KardexMateriaPrima.objects.filter(materia_prima=mp_cafe).order_by('fecha', 'id')
        cantidad_cafe_restante = quintales_cafe
        costo_total_cafe = Decimal('0')
        lotes_cafe = []
        for mov in movimientos_cafe:
            if mov.saldo_cantidad > 0 and cantidad_cafe_restante > 0:
                a_consumir = min(mov.saldo_cantidad, cantidad_cafe_restante)
                costo_total_cafe += a_consumir * mov.costo_unitario
                lotes_cafe.append({
                    "lote_id": mov.id,
                    "cantidad": a_consumir,
                    "costo_unitario": mov.costo_unitario,
                    "total": (a_consumir * mov.costo_unitario).quantize(Decimal('0.01')),
                })
                mov.saldo_cantidad -= a_consumir
                mov.saldo_total -= a_consumir * mov.costo_unitario
                mov.save()

                KardexMateriaPrima.objects.create(
                    materia_prima=mp_cafe,
                    fecha=timezone.now(),
                    tipo_movimiento='salida',
                    concepto="Consumo para Mezcla de Licor",
                    cantidad=a_consumir,
                    costo_unitario=mov.costo_unitario,
                    total=(a_consumir * mov.costo_unitario),
                    saldo_cantidad=mov.saldo_cantidad,
                    saldo_total=mov.saldo_total,
                )
                cantidad_cafe_restante -= a_consumir
            if cantidad_cafe_restante <= 0:
                break

        # --- Consumo de Licor
        movimientos_licor = KardexMateriaPrima.objects.filter(materia_prima=mp_licor).order_by('fecha', 'id')
        cantidad_licor_restante = litros_licor
        costo_total_licor = Decimal('0')
        lotes_licor = []
        for mov in movimientos_licor:
            if mov.saldo_cantidad > 0 and cantidad_licor_restante > 0:
                a_consumir = min(mov.saldo_cantidad, cantidad_licor_restante)
                costo_total_licor += a_consumir * mov.costo_unitario
                lotes_licor.append({
                    "lote_id": mov.id,
                    "cantidad": a_consumir,
                    "costo_unitario": mov.costo_unitario,
                    "total": (a_consumir * mov.costo_unitario).quantize(Decimal('0.01')),
                })
                mov.saldo_cantidad -= a_consumir
                mov.saldo_total -= a_consumir * mov.costo_unitario
                mov.save()

                KardexMateriaPrima.objects.create(
                    materia_prima=mp_licor,
                    fecha=timezone.now(),
                    tipo_movimiento='salida',
                    concepto="Consumo para Mezcla de Licor",
                    cantidad=a_consumir,
                    costo_unitario=mov.costo_unitario,
                    total=(a_consumir * mov.costo_unitario),
                    saldo_cantidad=mov.saldo_cantidad,
                    saldo_total=mov.saldo_total,
                )
                cantidad_licor_restante -= a_consumir
            if cantidad_licor_restante <= 0:
                break

        # --- Consumo de Agua
        movimientos_agua = KardexMateriaPrima.objects.filter(materia_prima=mp_agua).order_by('fecha', 'id')
        cantidad_agua_restante = garrafones_agua
        costo_total_agua = Decimal('0')
        lotes_agua = []
        for mov in movimientos_agua:
            if mov.saldo_cantidad > 0 and cantidad_agua_restante > 0:
                a_consumir = min(mov.saldo_cantidad, cantidad_agua_restante)
                costo_total_agua += a_consumir * mov.costo_unitario
                lotes_agua.append({
                    "lote_id": mov.id,
                    "cantidad": a_consumir,
                    "litros_usados": a_consumir * Decimal('20'),
                    "costo_unitario": mov.costo_unitario,
                    "total": (a_consumir * mov.costo_unitario).quantize(Decimal('0.01')),
                })
                mov.saldo_cantidad -= a_consumir
                mov.saldo_total -= a_consumir * mov.costo_unitario
                mov.save()

                KardexMateriaPrima.objects.create(
                    materia_prima=mp_agua,
                    fecha=timezone.now(),
                    tipo_movimiento='salida',
                    concepto="Consumo para Mezcla de Licor",
                    cantidad=a_consumir,
                    costo_unitario=mov.costo_unitario,
                    total=(a_consumir * mov.costo_unitario),
                    saldo_cantidad=mov.saldo_cantidad,
                    saldo_total=mov.saldo_total,
                )
                cantidad_agua_restante -= a_consumir
            if cantidad_agua_restante <= 0:
                break

        if cantidad_cafe_restante > 0 or cantidad_licor_restante > 0 or cantidad_agua_restante > 0:
            messages.error(request, "No hay suficiente materia prima para fabricar esa cantidad de licor de café.")
            return redirect('fabricar_mezcla_licor')

        # 3. Costos
        costo_mp = costo_total_cafe + costo_total_licor + costo_total_agua
        costo_mano_obra = (mano_obra_por_hora * horas_trabajadas).quantize(Decimal('0.01'))
        cif = ((costo_mp + costo_mano_obra) * Decimal('0.80')).quantize(Decimal('0.01'))
        costo_total = (costo_mp + costo_mano_obra + cif).quantize(Decimal('0.02'))

        producto_final = get_object_or_404(ProductoTerminado, nombre__iexact="Mezcla de Licor de Café")
        proceso = ProcesoFabricacion.objects.create(
            tipo='mezclar_licor',
            producto_final=producto_final,
            cantidad_producida=litros_a_fabricar,
            gramos_usados=Decimal('0'),
            quintales_usados=quintales_cafe,
            costo_materia_prima=costo_mp,
            costo_mano_obra=costo_mano_obra,
            cif=cif,
            costo_total=costo_total
        )

        # Kardex de Producto Terminado (entrada)
        ultimo_kardex = KardexProductoTerminado.objects.filter(producto=producto_final).order_by('-fecha', '-id').first()
        saldo_cantidad = (ultimo_kardex.saldo_cantidad if ultimo_kardex else Decimal('0')) + litros_a_fabricar
        saldo_total = (ultimo_kardex.saldo_total if ultimo_kardex else Decimal('0')) + costo_total

        KardexProductoTerminado.objects.create(
            producto=producto_final,
            fecha=timezone.now(),
            tipo_movimiento='ingreso',
            concepto=f"Fabricación de mezcla de licor (proceso {proceso.id})",
            cantidad=litros_a_fabricar,
            costo_unitario=(costo_total / litros_a_fabricar).quantize(Decimal('0.02')),
            total=costo_total,
            saldo_cantidad=saldo_cantidad,
            saldo_total=saldo_total,
        )

        context = {
            'proceso': proceso,
            'cafe_usado_quintales': quintales_cafe,
            'licor_usado_litros': litros_licor,
            'agua_usada_garrafones': garrafones_agua,
            'agua_usada_litros': litros_agua,
            'lotes_cafe': lotes_cafe,
            'lotes_licor': lotes_licor,
            'lotes_agua': lotes_agua,
        }
        return render(request, 'fabricacion/fabricar_mezclar_licor_exito.html', context)

    return render(request, 'fabricacion/fabricar_mezclar_licor.html')


#View para embotellar licor
def fabricar_embotellar_licor(request):
    if request.method == 'POST':
        try:
            botellas_a_fabricar = int(request.POST['cantidad_botellas'])
            mano_obra_por_hora = Decimal(request.POST['mano_obra_por_hora'])
            horas_trabajadas = Decimal(request.POST['horas_trabajadas'])
        except (KeyError, ValueError, InvalidOperation):
            messages.error(request, "Por favor ingresa valores válidos en todos los campos.")
            return redirect('fabricar_embotellar_licor')

        if botellas_a_fabricar <= 0:
            messages.error(request, "La cantidad de botellas debe ser mayor a cero.")
            return redirect('fabricar_embotellar_licor')
        if mano_obra_por_hora < 0 or horas_trabajadas < 0:
            messages.error(request, "El costo por hora y las horas trabajadas no pueden ser negativos.")
            return redirect('fabricar_embotellar_licor')

        # Cada botella necesita 0.75 litros de mezcla y 1 botella vacía
        litros_mezcla_necesarios = Decimal(botellas_a_fabricar) * Decimal('0.75')
        botellas_vacias_necesarias = Decimal(botellas_a_fabricar)

        # --- CONSUMO MEZCLA DE LICOR ---
        materia_prima_mezcla = get_object_or_404(ProductoTerminado, nombre__iexact="Mezcla de Licor de Café")
        movimientos_mezcla = KardexProductoTerminado.objects.filter(
            producto=materia_prima_mezcla
        ).order_by('fecha', 'id')

        cantidad_restante_mezcla = litros_mezcla_necesarios
        costo_total_mezcla = Decimal('0')
        consumido_lotes_mezcla = []

        for mov in movimientos_mezcla:
            if mov.saldo_cantidad > 0 and cantidad_restante_mezcla > 0:
                a_consumir = min(mov.saldo_cantidad, cantidad_restante_mezcla)
                costo_total_mezcla += a_consumir * mov.costo_unitario
                consumido_lotes_mezcla.append({
                    "lote_id": mov.id,
                    "cantidad": a_consumir,
                    "costo_unitario": mov.costo_unitario,
                    "total": (a_consumir * mov.costo_unitario).quantize(Decimal('0.01')),
                })
                nueva_saldo_cantidad = mov.saldo_cantidad - a_consumir
                nueva_saldo_total = mov.saldo_total - (a_consumir * mov.costo_unitario)
                KardexProductoTerminado.objects.create(
                    producto=materia_prima_mezcla,
                    fecha=timezone.now(),
                    tipo_movimiento='salida',
                    concepto=f"Consumo para embotellado de licor",
                    cantidad=a_consumir,
                    costo_unitario=mov.costo_unitario,
                    total=(a_consumir * mov.costo_unitario),
                    saldo_cantidad=nueva_saldo_cantidad,
                    saldo_total=nueva_saldo_total,
                )
                mov.saldo_cantidad = nueva_saldo_cantidad
                mov.saldo_total = nueva_saldo_total
                mov.save()
                cantidad_restante_mezcla -= a_consumir
            if cantidad_restante_mezcla <= 0:
                break

        if cantidad_restante_mezcla > 0:
            messages.error(request, "No hay suficiente mezcla de licor para fabricar esa cantidad de botellas.")
            return redirect('fabricar_embotellar_licor')

        # --- CONSUMO BOTELLAS VACÍAS ---
        materia_prima_botella = get_object_or_404(MateriaPrima, nombre__iexact="Botellas de vidrio de 750ml")
        movimientos_botella = KardexMateriaPrima.objects.filter(
            materia_prima=materia_prima_botella
        ).order_by('fecha', 'id')

        cantidad_restante_botella = botellas_vacias_necesarias
        costo_total_botellas = Decimal('0')
        consumido_lotes_botella = []

        for mov in movimientos_botella:
            if mov.saldo_cantidad > 0 and cantidad_restante_botella > 0:
                a_consumir = min(mov.saldo_cantidad, cantidad_restante_botella)
                costo_total_botellas += a_consumir * mov.costo_unitario
                consumido_lotes_botella.append({
                    "lote_id": mov.id,
                    "cantidad": a_consumir,
                    "costo_unitario": mov.costo_unitario,
                    "total": (a_consumir * mov.costo_unitario).quantize(Decimal('0.01')),
                })
                nueva_saldo_cantidad = mov.saldo_cantidad - a_consumir
                nueva_saldo_total = mov.saldo_total - (a_consumir * mov.costo_unitario)
                KardexMateriaPrima.objects.create(
                    materia_prima=materia_prima_botella,
                    fecha=timezone.now(),
                    tipo_movimiento='salida',
                    concepto=f"Consumo para embotellado de licor",
                    cantidad=a_consumir,
                    costo_unitario=mov.costo_unitario,
                    total=(a_consumir * mov.costo_unitario),
                    saldo_cantidad=nueva_saldo_cantidad,
                    saldo_total=nueva_saldo_total,
                )
                mov.saldo_cantidad = nueva_saldo_cantidad
                mov.saldo_total = nueva_saldo_total
                mov.save()
                cantidad_restante_botella -= a_consumir
            if cantidad_restante_botella <= 0:
                break

        if cantidad_restante_botella > 0:
            messages.error(request, "No hay suficientes botellas vacías en inventario.")
            return redirect('fabricar_embotellar_licor')

        # --- MANO DE OBRA Y CIF ---
        costo_mano_obra = (mano_obra_por_hora * horas_trabajadas).quantize(Decimal('0.01'))
        costo_total_mp = costo_total_mezcla + costo_total_botellas

        cif_mezcla = Decimal('0.80')  # 80% para mezcla
        cif_emb = Decimal('0.45')     # 45% para embotellado

        # Cálculo de CIF y costo total
        cif = ((costo_total_mp + costo_mano_obra) * cif_emb).quantize(Decimal('0.01'))
        costo_total = (costo_total_mp + costo_mano_obra + cif).quantize(Decimal('0.01'))

        # --- CALCULAR EL PRECIO DE VENTA UNITARIO ---
        # Recupera el costo total de mezcla usado para esta tanda de embotellado:
        costo_mezcla_consumida = costo_total_mezcla
        costo_embotellado = costo_total - costo_total_mezcla

        suma_costos = costo_mezcla_consumida + costo_embotellado
        margen = Decimal('0.50')  # 50% margen (puedes ajustar aquí)
        precio_venta_unitario = (suma_costos / Decimal(botellas_a_fabricar)) * (1 + margen)
        precio_venta_unitario = precio_venta_unitario.quantize(Decimal('0.02'))

        # --- REGISTRO DE PROCESO ---
        producto_final = get_object_or_404(ProductoTerminado, nombre__iexact="Licor de Café 750ml")
        proceso = ProcesoFabricacion.objects.create(
            tipo='embotellar_licor',
            producto_final=producto_final,
            cantidad_producida=botellas_a_fabricar,
            gramos_usados=litros_mezcla_necesarios,  # Guardamos litros usados en este campo
            quintales_usados=botellas_vacias_necesarias,  # Guardamos botellas usadas en este campo
            costo_materia_prima=costo_total_mp,
            costo_mano_obra=costo_mano_obra,
            cif=cif,
            costo_total=costo_total
        )

        # --- ENTRADA AL KARDEX DE PRODUCTO TERMINADO ---
        ultimo_kardex = KardexProductoTerminado.objects.filter(
            producto=producto_final
        ).order_by('-fecha', '-id').first()
        saldo_cantidad = (ultimo_kardex.saldo_cantidad if ultimo_kardex else Decimal('0')) + Decimal(botellas_a_fabricar)
        saldo_total = (ultimo_kardex.saldo_total if ultimo_kardex else Decimal('0')) + costo_total

        KardexProductoTerminado.objects.create(
            producto=producto_final,
            fecha=timezone.now(),
            tipo_movimiento='ingreso',
            concepto=f"Embotellado por proceso {proceso.id}",
            cantidad=Decimal(botellas_a_fabricar),
            costo_unitario=(costo_total / Decimal(botellas_a_fabricar)).quantize(Decimal('0.01')),
            total=costo_total,
            saldo_cantidad=saldo_cantidad,
            saldo_total=saldo_total,
            precio_venta_unitario=precio_venta_unitario,   # <-- aquí se almacena el precio de venta unitario
        )

        messages.success(request, f"Embotellado registrado exitosamente. Costo total: ${costo_total:,.2f}")
        crear_asiento_venta(
            producto_final,
            cantidad=botellas_a_fabricar,
            costo_unitario=(costo_total / Decimal(botellas_a_fabricar)).quantize(Decimal('0.01')),
            precio_venta_unitario=precio_venta_unitario,
            porcentaje_iva=Decimal('13')
        )
        return render(request, 'fabricacion/fabricar_embotellar_licor_exito.html', {
            'proceso': proceso,
            'consumido_lotes_mezcla': consumido_lotes_mezcla,
            'consumido_lotes_botella': consumido_lotes_botella,
            'costo_mezcla': costo_mezcla_consumida,
            'costo_embotellado': costo_embotellado,
            'precio_venta_unitario': precio_venta_unitario,
        })

    return render(request, 'fabricacion/fabricar_embotellar_licor.html')