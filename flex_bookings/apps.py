from django.apps import AppConfig

class FlexBookingConfig(AppConfig):
    name = 'flex_bookings'

    def ready(self):
        import flex_bookings.signals
