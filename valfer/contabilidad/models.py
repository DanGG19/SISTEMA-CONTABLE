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

#Modelo para Inventario Perpetuo
class Producto(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)  # Costo unitario
    stock = models.IntegerField(default=0)
    cuenta_inventario = models.ForeignKey(CuentaContable, on_delete=models.PROTECT, related_name='productos_inventario')  # Ej: 1105.01
    cuenta_ingresos = models.ForeignKey(CuentaContable, on_delete=models.PROTECT, related_name='productos_ingresos')  # Ej: 5101.01
    cuenta_costo_venta = models.ForeignKey(CuentaContable, on_delete=models.PROTECT, related_name='productos_costo')  # Ej: 4101.01

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class MovimientoInventario(models.Model):
    TIPO_CHOICES = [('compra', 'Compra'), ('venta', 'Venta')]
    fecha = models.DateField()
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0.13)  # 13% IVA
    asiento = models.ForeignKey(AsientoContable, on_delete=models.SET_NULL, null=True, blank=True)
    
    def calcular_total(self):
        """Calcula el total (cantidad × precio_unitario)"""
        try:
            return round(float(self.cantidad) * float(self.precio_unitario), 2)
        except (TypeError, ValueError):
            return 0.0

    def __str__(self):
        return f"{self.tipo.upper()} - {self.producto.nombre} x{self.cantidad}"
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
    

#Para costos de ABC
MESES_CHOICES = [
    ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
    ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
    ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
]

ANIOS_CHOICES = [(str(y), str(y)) for y in range(2020, 2031)]  # Año como (valor, etiqueta)

class Actividad(models.Model):
    nombre = models.CharField(max_length=100)
    unidad_medida = models.CharField(max_length=50)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    mes = models.CharField(max_length=2, choices=MESES_CHOICES, blank=True, null=True)
    anio = models.CharField(max_length=4, choices=ANIOS_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.nombre
    

class AsignacionActividad(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    cantidad_consumo = models.DecimalField(max_digits=12, decimal_places=2)  # Ej: 15,000 hr-maq para Mica simple

    # Este valor lo calculamos: valor_consumo = cantidad_consumo * tasa_asignacion
    valor_consumo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f'{self.actividad.nombre} para {self.producto.nombre}'

class CostoDirecto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    mano_obra_directa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    materia_prima_directa = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    limpieza_moldes = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def total_costos_directos(self):
        return self.mano_obra_directa + self.materia_prima_directa + self.limpieza_moldes

class CostoTotalProducto(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE)
    costo_indirecto = models.DecimalField(max_digits=12, decimal_places=2)
    costo_directo = models.DecimalField(max_digits=12, decimal_places=2)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_producida = models.PositiveIntegerField(default=0)  # Ej: 55,000 unidades para Mica simple

    def __str__(self):
        return f'Costo total de {self.producto.nombre}'



