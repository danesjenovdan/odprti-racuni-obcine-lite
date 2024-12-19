from django.apps import AppConfig


class ObcineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "obcine"

    def ready(self):
        import obcine.signals
