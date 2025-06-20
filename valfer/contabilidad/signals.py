from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import *
import logging
from django.core.management import call_command

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
                'nombre': 'Café en Quintales para tostar',
                'unidad_medida': 'quintal'
            },
            {
                'nombre': 'Café en Quintales para Licor',
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
            ,
            {
                'nombre': 'Garrafón de agua',
                'unidad_medida': 'garrafa'
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

# Signal para crear productos terminados automáticamente
@receiver(post_migrate)
def crear_productos_terminados_iniciales(sender, **kwargs):
    """
    Crea productos terminados predefinidos después de ejecutar las migraciones
    """
    if sender.name == 'contabilidad':
        productos_terminados_iniciales = [
            {
                'nombre': 'Bolsa Café 400g',  # Debe coincidir con el que busca tu view
                'unidad_medida': 'bolsa'
            },
             {
                'nombre': 'Mezcla de Licor de Café',  # <--- ¡Agrega esto!
                'unidad_medida': 'litro'
            },
            {
                'nombre': 'Licor de Café 750ml',
                'unidad_medida': 'botella'
            }
        ]
        
        for producto_data in productos_terminados_iniciales:
            producto, created = ProductoTerminado.objects.get_or_create(
                nombre=producto_data['nombre'],
                defaults=producto_data
            )
            if created:
                logger.info(f"Producto Terminado creado: {producto.nombre}")
            else:
                logger.info(f"Producto Terminado ya existe: {producto.nombre}")

# Signal para cargar el fixture después de migraciones
@receiver(post_migrate)
def cargar_fixture_catalogo(sender, **kwargs):
    """
    Carga los datos iniciales desde catalogo_valfer.json
    """
    if sender.name == 'contabilidad':
        try:
            call_command('loaddata', 'catalogo_valfer.json')
            logger.info("Fixture catalogo_valfer.json cargado exitosamente")
        except Exception as e:
            logger.error(f"Error al cargar el fixture: {str(e)}")