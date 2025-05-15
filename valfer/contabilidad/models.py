from django.db import models

# Create your models here.
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

