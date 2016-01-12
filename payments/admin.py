from django.contrib import admin
from payments.models import PaypalBookingTransaction, PaypalBlockTransaction


class PaypalBookingTransactionAdmin(admin.ModelAdmin):

    list_display = ('id', 'get_user', 'get_event', 'invoice_id',
                    'transaction_id')
    readonly_fields = ('id', 'booking', 'get_user', 'get_event', 'invoice_id',
                    'transaction_id', 'get_booking_id', 'cost')

    def get_booking_id(self, obj):
        return obj.booking.id
    get_booking_id.short_description = "Booking id"

    def get_user(self, obj):
        return "{} {}".format(
            obj.booking.user.first_name, obj.booking.user.last_name
        )
    get_user.short_description = "User"

    def get_event(self, obj):
        return obj.booking.event
    get_event.short_description = "Event"

    def cost(self, obj):
        return u"\u00A3{:.2f}".format(obj.booking.event.cost)


class PaypalBlockTransactionAdmin(admin.ModelAdmin):

    list_display = ('id', 'get_user', 'invoice_id',
                    'transaction_id')
    readonly_fields = ('block', 'id', 'get_user', 'invoice_id',
                    'transaction_id', 'get_block_id', 'cost')


    def get_block_id(self, obj):
        return obj.block.id
    get_block_id.short_description = "Block id"

    def get_user(self, obj):
        return "{} {}".format(
            obj.block.bookings.first().user.first_name,
            obj.block.bookings.first().user.last_name
        )
    get_user.short_description = "User"

    def cost(self, obj):
        return u"\u00A3{:.2f}".format(
            obj.block.item_cost * obj.block.bookings.count()
        )


admin.site.register(PaypalBookingTransaction, PaypalBookingTransactionAdmin)
admin.site.register(PaypalBlockTransaction, PaypalBlockTransactionAdmin)
