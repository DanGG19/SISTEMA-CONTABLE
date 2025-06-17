from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import *
import logging

logger = logging.getLogger(__name__)

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

# Signal para crear materias primas automáticamente
@receiver(post_migrate)
def crear_materias_primas_iniciales(sender, **kwargs):
    """
    Crea materias primas predefinidas después de ejecutar las migraciones
    """
    if sender.name == 'contabilidad':
        materias_primas_iniciales = [
            {
                'nombre': 'Café en Quintales',
                'unidad_medida': 'quintal'
            },
            {
                'nombre': 'Botellas de vidrio de 750ml',
                'unidad_medida': 'unidad'
            },
            {
                'nombre': 'Botella de licor',
                'unidad_medida': 'botella'
            }
        ]
        
        for materia_data in materias_primas_iniciales:
            materia_prima, created = MateriaPrima.objects.get_or_create(
                nombre=materia_data['nombre'],
                defaults=materia_data
            )
            if created:
                logger.info(f"Materia Prima creada: {materia_prima.nombre}")
            else:
                logger.info(f"Materia Prima ya existe: {materia_prima.nombre}")