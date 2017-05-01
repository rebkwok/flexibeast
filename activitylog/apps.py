from django.apps import AppConfig

class ActivityLogConfig(AppConfig):
    name = 'activitylog'

    def ready(self):
        import activitylog.signals
