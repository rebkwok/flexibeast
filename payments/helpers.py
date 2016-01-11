import random
from django.db import IntegrityError

from payments.models import PaypalBookingTransaction, PaypalBlockTransaction


def create_booking_paypal_transaction(user, booking):
    id_string = "-".join([user.username] +
                         ["".join([word[0] for word in
                                   booking.event.name.split()])] +
                         [booking.event.date.strftime("%d%m%y%H%M")] + ['inv#'])
    existing = PaypalBookingTransaction.objects.filter(
        invoice_id__contains=id_string, booking=booking).order_by('-invoice_id')

    if existing:
        # PaypalBookingTransaction is created when the view is called, not when
        # payment is made.  If there is no transaction id stored against it,
        # we shouldn't need to make a new one
        for transaction in existing:
            if not transaction.transaction_id:
                return transaction
        existing_counter = existing[0].invoice_id[-3:]
        counter = str(int(existing_counter) + 1).zfill(len(existing_counter))
    else:
        counter = '001'

    pbt = PaypalBookingTransaction.objects.filter(
        invoice_id=id_string+counter
    )
    if pbt:
        # in case we end up creating a duplicate invoice id for a different
        # booking (the check for existing above checked for this exact
        # combination of invoice id and booking
        random_prefix = random.randrange(100,999)
        pbt = PaypalBookingTransaction.objects.create(
            invoice_id=id_string+str(random_prefix)+counter, booking=booking
        )
    else:
        pbt = PaypalBookingTransaction.objects.create(
        invoice_id=id_string+counter, booking=booking
    )
    return pbt


def create_block_paypal_transaction(user, block):

    id_string = "-".join([user.username] +
                         ["".join([word[0] for word in
                          block.name.split()])] + ['inv#'])

    existing = PaypalBlockTransaction.objects.filter(
        invoice_id__contains=id_string, block=block).order_by('-invoice_id')

    if existing:
        # PaypalBlockTransaction is created when the view is called, not when
        # payment is made.  If there is no transaction id stored against it,
        # we shouldn't need to make a new one
        for transaction in existing:
            if not transaction.transaction_id:
                return transaction
        existing_counter = existing[0].invoice_id[-3:]
        counter = str(int(existing_counter) + 1).zfill(len(existing_counter))
    else:
        counter = '001'
    pbt = PaypalBlockTransaction.objects.filter(
        invoice_id=id_string+counter
    )
    # in case we end up creating a duplicate invoice id for a different
    # block (the check for existing above checked for this exact
    # combination of invoice id and block
    if pbt:
        random_prefix = random.randrange(100,999)
        pbt = PaypalBlockTransaction.objects.create(
            invoice_id=id_string+str(random_prefix)+counter, block=block
        )
    else:
        pbt = PaypalBlockTransaction.objects.create(
            invoice_id=id_string+counter, block=block
        )
    return pbt
