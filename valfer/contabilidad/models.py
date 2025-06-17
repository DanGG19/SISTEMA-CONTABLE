from django.db import models

TIPOS_CUENTA = [
    ('activo', 'Activo'),
    ('pasivo', 'Pasivo'),
    ('patrimonio', 'Patrimonio'),
    ('costo', 'Costo'),
    ('gasto', 'Gasto'),
    ('ingreso', 'Ingreso'),
    ('liquidadora', 'Liquidadora'),
]

class CuentaContable(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50, choices=TIPOS_CUENTA)
    nivel = models.IntegerField()
    padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class AsientoContable(models.Model):
    fecha = models.DateField()
    descripcion = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Asiento #{self.id} - {self.fecha}"

# models.py
class DetalleAsiento(models.Model):
    asiento = models.ForeignKey(AsientoContable, on_delete=models.CASCADE)
    fecha = models.DateField(null=True, blank=True)
    descripcion = models.CharField(max_length=255, blank=True)
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.CASCADE)
    debe = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    haber = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.fecha} - {self.descripcion} - {self.cuenta.codigo}"

# modelos para Planillas de Salarios 

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    dui = models.CharField(max_length=10)
    nit = models.CharField(max_length=17)
    cargo = models.CharField(max_length=100)
    salario_base = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

class Planilla(models.Model):
    MES_CHOICES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]

    mes = models.IntegerField(choices=MES_CHOICES)
    anio = models.IntegerField()
    descripcion = models.CharField(max_length=255)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Planilla {self.get_mes_display()} {self.anio}"

class DetallePlanilla(models.Model):
    planilla = models.ForeignKey(Planilla, related_name='detalles', on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    dias_trabajados = models.IntegerField()
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    afp = models.DecimalField(max_digits=10, decimal_places=2)
    isss = models.DecimalField(max_digits=10, decimal_places=2)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    total_costo_empleador = models.DecimalField(max_digits=10, decimal_places=2, default=0)


#MOdelo para el balance general
class BalanceGeneral(models.Model):
    fecha_generado = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    total_activo = models.DecimalField(max_digits=12, decimal_places=2)
    total_pasivo = models.DecimalField(max_digits=12, decimal_places=2)
    total_patrimonio = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Balance del {self.fecha_inicio} al {self.fecha_fin}"

class DetalleBalance(models.Model):
    balance = models.ForeignKey(BalanceGeneral, on_delete=models.CASCADE, related_name='detalles')
    cuenta = models.ForeignKey('CuentaContable', on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cuenta} - {self.saldo}"

#Modelo para el estado de resultados
class EstadoResultados(models.Model):
    fecha_generado = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    total_ingresos = models.DecimalField(max_digits=12, decimal_places=2)
    total_gastos = models.DecimalField(max_digits=12, decimal_places=2)
    utilidad_neta = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Resultado del {self.fecha_inicio} al {self.fecha_fin}"

class DetalleResultado(models.Model):
    estado = models.ForeignKey(EstadoResultados, on_delete=models.CASCADE, related_name='detalles')
    cuenta = models.ForeignKey(CuentaContable, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cuenta} - {self.monto}"
    
#Modelos para Materia Prima y Producto Terminado
class MateriaPrima(models.Model):
    nombre = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=20)  # Ej: 'quintal', 'botella', 'litro'

    def __str__(self):
        return self.nombre

class ProductoTerminado(models.Model):
    nombre = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=20)  # Ej: 'bolsa 400g', 'botella 750ml'

    def __str__(self):
        return self.nombre

#Modelo para Kardex de Materia Prima
class KardexMateriaPrima(models.Model):
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo_movimiento = models.CharField(max_length=20, choices=[('entrada','Entrada'),('salida','Salida'),('proceso','Consumo Proceso')])
    concepto = models.CharField(max_length=255, blank=True, null=True)  # Ej: factura, proceso, etc.
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.materia_prima} - {self.fecha} - {self.tipo_movimiento}"

#Modelo para Kardex de Producto Terminado
class KardexProductoTerminado(models.Model):
    producto = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo_movimiento = models.CharField(max_length=20, choices=[('ingreso','Ingreso Proceso'),('salida','Venta')])
    concepto = models.CharField(max_length=255, blank=True, null=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto} - {self.fecha} - {self.tipo_movimiento}"

#Modelos para Procesos de Producción
class ProcesoProduccion(models.Model):
    fecha = models.DateField()
    tipo = models.CharField(max_length=30, choices=[('mezcla','Mezcla Licor'),('embazado','Embazado'),('tostado','Tostado')])
    cantidad_producida = models.DecimalField(max_digits=12, decimal_places=2)
    producto_terminado = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.producto_terminado} - {self.fecha}"

class ConsumoMateriaPrima(models.Model):
    proceso = models.ForeignKey(ProcesoProduccion, related_name="consumos", on_delete=models.CASCADE)
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.CASCADE)
    cantidad_usada = models.DecimalField(max_digits=12, decimal_places=2)
    costo_asignado = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.materia_prima} ({self.cantidad_usada}) en {self.proceso}"

class ProcesoFabricacion(models.Model):
    TIPO_CHOICES = [
        ('embolsar_cafe', 'Embolsar Café'),
        ('mezclar_licor', 'Mezcla Café con Licor'),
        ('embotellar_licor', 'Embotellado Café con Licor'),
    ]
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    fecha = models.DateField(auto_now_add=True)
    producto_final = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    cantidad_producida = models.IntegerField()
    gramos_usados = models.DecimalField(max_digits=10, decimal_places=2)
    quintales_usados = models.DecimalField(max_digits=10, decimal_places=2)
    costo_materia_prima = models.DecimalField(max_digits=12, decimal_places=2)
    costo_mano_obra = models.DecimalField(max_digits=12, decimal_places=2)
    cif = models.DecimalField(max_digits=12, decimal_places=2)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
