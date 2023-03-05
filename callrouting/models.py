# Standard Library Imports
import datetime

# Django Imports
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

# 3rd Party Imports
from phonenumber_field.modelfields import PhoneNumberField
from solo.models import SingletonModel


# Create your models here.

def yesterday():
    return datetime.date.today() - datetime.timedelta(days=1)

class EmailState(SingletonModel):
    in_progress = models.BooleanField(default=False)
    last_sent = models.DateField(default=yesterday)

class UserGroup(models.Model):
    class DefaultAction(models.TextChoices):
        VOICEMAIL = 'Voicemail'
        DEFAULT_DESTINATION = 'Default Destination'

    name = models.CharField(max_length=150)
    incoming_number = PhoneNumberField("Incoming Number")
    greeting = models.CharField(max_length=200)
    # Should the default action be a phone number or voicemail?
    default_action = models.CharField(choices=DefaultAction.choices,
        max_length=25, default=DefaultAction.DEFAULT_DESTINATION)
    # If the default is not voicemail, and there's no volunteer, what
    # number does the call go to?
    default_destination = PhoneNumberField("Default Destination")
    # Voicemail destination email address
    voicemail_email = models.EmailField(default='default@domain.local')
    # Voicemail greeting message
    voicemail_greeting = models.CharField(max_length=200, default='')

    def __str__(self):
        return self.name

class Volunteer(models.Model):
    name = models.CharField('Name', max_length=200)
    number = PhoneNumberField('Phone Number')
    email = models.EmailField()
    send_emails = models.BooleanField(default=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

hour_labels = {
    6: '6AM',
    7: '7AM',
    8: '8AM',
    9: '9AM',
    10: '10AM',
    11: '11AM',
    12: 'Midday',
    13: '1PM',
    14: '2PM',
    15: '3PM',
    16: '4PM',
    17: '5PM',
    18: '6PM',
    19: '7PM',
    20: '8PM',
    21: '9PM',
    22: '10PM',
    23: '11PM',
}

class Shift(models.Model):
    class ShiftHour(models.IntegerChoices):
        HOUR_6 = 6, hour_labels[6]
        HOUR_7 = 7, hour_labels[7]
        HOUR_8 = 8, hour_labels[8]
        HOUR_9 = 9, hour_labels[9]
        HOUR_10 = 10, hour_labels[10]
        HOUR_11 = 11, hour_labels[11]
        HOUR_12 = 12, hour_labels[12]
        HOUR_13 = 13, hour_labels[13]
        HOUR_14 = 14, hour_labels[14]
        HOUR_15 = 15, hour_labels[15]
        HOUR_16 = 16, hour_labels[16]
        HOUR_17 = 17, hour_labels[17]
        HOUR_18 = 18, hour_labels[18]
        HOUR_19 = 19, hour_labels[19]
        HOUR_20 = 20, hour_labels[20]
        HOUR_21 = 21, hour_labels[21]
        HOUR_22 = 22, hour_labels[22]
        HOUR_23 = 23, hour_labels[23]

    class ShiftDay(models.TextChoices):
        MONDAY = 'Monday'
        TUESDAY = 'Tuesday'
        WEDNESDAY = 'Wednesday'
        THURSDAY = 'Thursday'
        FRIDAY = 'Friday'
        SATURDAY = 'Saturday'
        SUNDAY = 'Sunday'

    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    day = models.CharField(choices=ShiftDay.choices, max_length=10)
    start_time = models.IntegerField(choices=ShiftHour.choices)
    end_time = models.IntegerField(choices=ShiftHour.choices)
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)

    def clean(self):
        if self.user_group != self.volunteer.user_group:
            raise ValidationError('User group of shift must match user group')

    def __str__(self):
        start = hour_labels[self.start_time]
        end = hour_labels[self.end_time]
        return "%s: %s, %s %s-%s" % (self.user_group, self.volunteer, self.day, start, end)

class Call(models.Model):
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)

    # Call properties
    sid = models.CharField('Call SID', max_length=34, primary_key=True)
    caller_number = PhoneNumberField('Caller Number')
    called_number = PhoneNumberField('Called Number')
    time = models.DateTimeField('Time', auto_now_add=True)

    # Recording / transcription properties
    recording_begun = models.BooleanField('Recording begun', default=False)
    recording_received = models.BooleanField('Recording received', default=False)
    recording_url = models.URLField('Recording URL', null=True)
    transcription_received = models.BooleanField('Transcription received', default=False)
    transcription_successful = models.BooleanField('Transcription successful', default=False)
    transcription_text = models.CharField('Transcription text', max_length=8192, null=True)

    # Email properties
    email_attempted = models.BooleanField('Email attempted', default=False)
    email_send_time = models.DateTimeField('Email send time', null=True)
    email_send_finished = models.BooleanField('Email send finished', default=False)

    def __str__(self):
        return f'{self.time}: {self.sid}'
