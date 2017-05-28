# -*- coding: utf-8 -*-

from django.db import models


MON = '01MON'
TUE = '02TUE'
WED = '03WED'
THU = '04THU'
FRI = '05FRI'
SAT = '06SAT'
SUN = '07SUN'
DAY_CHOICES = (
    (MON, 'Monday'),
    (TUE, 'Tuesday'),
    (WED, 'Wednesday'),
    (THU, 'Thursday'),
    (FRI, 'Friday'),
    (SAT, 'Saturday'),
    (SUN, 'Sunday')
)


class Location(models.Model):
    short_name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default="")
    map_url = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.short_name


class WeeklySession(models.Model):
    """
    An interim timetable session model while booking is not implemented for
    FlexiBeast site.  Will be used to maintain/display weekly timetable; to
    also include block info.
    """

    MON = '01MON'
    TUE = '02TUE'
    WED = '03WED'
    THU = '04THU'
    FRI = '05FRI'
    SAT = '06SAT'
    SUN = '07SUN'
    DAY_CHOICES = (
        (MON, 'Monday'),
        (TUE, 'Tuesday'),
        (WED, 'Wednesday'),
        (THU, 'Thursday'),
        (FRI, 'Friday'),
        (SAT, 'Saturday'),
        (SUN, 'Sunday')
    )

    name = models.CharField(max_length=255)
    day = models.CharField(max_length=5, choices=DAY_CHOICES)
    time = models.TimeField()
    # event_type = models.ForeignKey(EventType, null=True)
    description = models.TextField(blank=True, default="")
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL
    )
    max_participants = models.PositiveIntegerField(
        null=True, blank=True, default=9,
        help_text="Leave blank if no max number of participants"
    )
    contact_person = models.CharField(max_length=255, default="Alicia Alexandra")
    contact_email = models.EmailField(default="flexibeast@hotmail.com")
    cost = models.DecimalField(default=7.00, max_digits=8, decimal_places=2)

    full = models.BooleanField(default=False)
    block_info = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ('day', 'time')

    def __str__(self):
        return "{} - {} {}".format(
            self.name, dict(self.DAY_CHOICES)[self.day],
            self.time.strftime('%H:%M')
        )


class StretchClinic(models.Model):
    date = models.DateField()
    description = models.TextField(blank=True, default="")
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL
    )
    max_participants = models.PositiveIntegerField(
        null=True, blank=True, default=9,
        help_text="Leave blank if no max number of participants"
    )
    contact_person = models.CharField(max_length=255, default="Alicia Alexandra")
    contact_email = models.EmailField(default="flexibeast@hotmail.com")
    cost = models.DecimalField(
        default=30.00, max_digits=8, decimal_places=2,
        help_text='Cost (£) per hour'
    )
    spaces = models.PositiveIntegerField()
    show_on_site = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.id and self.spaces is None or self.spaces == '':
            self.spaces = self.max_participants

        super(StretchClinic, self).save(*args, **kwargs)

    def __str__(self):
        return "Stretch Clinic - {}".format(
            self.date.strftime('%d %b %y %H:%M')
        )
