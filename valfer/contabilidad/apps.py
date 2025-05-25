from django.apps import AppConfig

class ContabilidadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contabilidad'

    def ready(self):
        # Importa las señales solo después de que Django esté listo
        import contabilidad.signals 