from django.apps import AppConfig

class TraceabilityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'traceability'

    def ready(self):
        import traceability.signals  # Charge les signaux