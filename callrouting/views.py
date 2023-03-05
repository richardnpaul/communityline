# Standard Library Imports
from datetime import datetime
import logging
import sys

# Django Imports
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

# 3rd Party Imports
from django_twilio.decorators import twilio_view
from django_twilio.request import decompose
import pytz
from twilio.twiml.voice_response import VoiceResponse

# App Imports
from callrouting.models import Call, Shift, UserGroup, hour_labels


# Create your views here.




logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def get_shifts(user_group, day, hour):
    """
    Return all active shifts on a given day and hour.
    """
    return Shift.objects.filter(day__exact=day, start_time__lte=hour,
                                end_time__gt=hour, user_group__exact=user_group)

def get_current_volunteer(user_group):
    """
    Get the current volunteer according to the shift pattern.

    If there are multiple volunteers, simply return the first.

    If there are no volunteers, return None.
    """

    now = datetime.now(pytz.timezone('Europe/London'))
    day = now.strftime('%A')
    hour = now.hour
    shifts = get_shifts(user_group, day, hour)
    if shifts:
        return shifts[0].volunteer
    return None

@login_required
def volunteers(request, user_group_id, day, hour):
    """
    For inspecting the available volunteers at a given time.
    """
    user_group = UserGroup.objects.get(id=user_group_id)

    context = {
        'day': day,
        'hour': hour_labels.get(hour, 'out of hours'),
        'shifts': get_shifts(user_group, day, hour),
        'user_group': user_group
    }

    return HttpResponse(render(request, 'callrouting/volunteers.html', context))

def get_current_destination(user_group):
    """
    Get the current destination phone number.
    """
    current_volunteer = get_current_volunteer(user_group)
    if current_volunteer:
        return current_volunteer.number.as_e164
    else:
        return user_group.default_destination.as_e164

def build_forward_response(greeting, dial_number):
    r = VoiceResponse()
    r.say(greeting, voice='woman', language='en-gb')
    r.dial(dial_number)
    return r

def build_voicemail_response(user_group, twilio_request):
    try:
        Call.objects.create(user_group=user_group, sid=twilio_request.callsid,
            caller_number=twilio_request.from_, called_number=twilio_request.to)
    except Exception as exc:
        logger.error(f'Error creating call object: {exc.args[0]}')
        raise

    r = VoiceResponse()
    r.say(user_group.voicemail_greeting, voice='woman', language='en-gb')
    r.record(action='recording', finish_on_key='*', timeout=120,
        recording_status_callback='recordingcomplete', transcribe=True,
        transcribe_callback='transcription')
    return r

def build_response(user_group, twilio_request):
    destination = get_current_volunteer(user_group)

    if destination is None:
        if user_group.default_action == UserGroup.DefaultAction.VOICEMAIL:
            return build_voicemail_response(user_group, twilio_request)
        else:
            dial_number = user_group.default_destination.as_e164
    else:
        dial_number = destination.number.as_e164

    greeting = user_group.greeting
    return build_forward_response(greeting, dial_number)

@twilio_view
def handle(request):
    twilio_request = decompose(request)
    called_number = twilio_request.to

    try:
        user_group = UserGroup.objects.get(incoming_number=called_number)
    except UserGroup.DoesNotExist:
        logger.error(f"No user group found for {called_number}")
        raise

    return build_response(user_group, twilio_request)

def get_call_for_update(sid):
    return Call.objects.filter(sid=sid).select_for_update().get()

@twilio_view
def recording(request):
    twilio_request = decompose(request)
    with transaction.atomic():
        call = get_call_for_update(twilio_request.callsid)
        call.recording_begun = True
        call.save()
    return HttpResponse()

def send_email_if_necessary(sid):
    # Phase 1: check if the conditions for sending the email are met:
    # - We should have received both the recording and the transcription
    # - We should not have already attempted to send the email
    with transaction.atomic():
        call = get_call_for_update(sid)
        if call.transcription_received and call.recording_received and not call.email_attempted:
            call.email_attempted = True
            call.email_send_time = datetime.now(pytz.timezone('Europe/London'))
            call.save()

            # Grab relevant fields from the call record to put into the email notification
            caller_number = call.caller_number
            recording_url = call.recording_url
            user_group_name = call.user_group.name
            receiver = call.user_group.voicemail_email

            # The transcription may not be available if it failed for some reason
            transcription_successful = call.transcription_successful
            if call.transcription_successful:
                transcription_text = call.transcription_text
        else:
            # Don't do anything right now
            return

    # Phase 2: email the recording and transaction to the user group message email
    subject = f'Community Line: new voicemail from {caller_number}'

    if transcription_successful:
        context = {'transcription_text': transcription_text}
        html_transcription = render_to_string('callrouting/transcription_successful_fragment.html', context)
        text_transcription = render_to_string('callrouting/transcription_successful_fragment.txt', context)
    else:
        html_transcription = mark_safe("<p>No transcription of the call is available.</p>")
        text_transcription = "No transcription of the call is available."

    context = {
        'caller_number': caller_number,
        'recording_url': recording_url,
        'html_transcription': html_transcription,
        'text_transcription': text_transcription,
        'user_group_name': user_group_name,
    }
    text_message = render_to_string('callrouting/voicemail_email.txt', context)
    html_message = render_to_string('callrouting/voicemail_email.html', context)
    sender = 'Community Line <communityline@domain.local>'

    send_mail(subject, text_message, sender, [receiver], html_message=html_message, fail_silently=False)

    # Phase 3: record that we successfully sent the mail if we get here
    with transaction.atomic():
        call = get_call_for_update(sid)
        call.email_send_finished = True
        call.save()

@twilio_view
def recordingcomplete(request):
    twilio_request = decompose(request)
    sid = twilio_request.callsid

    with transaction.atomic():
        call = get_call_for_update(sid)
        call.recording_received = True
        call.recording_url = twilio_request.recordingurl
        call.save()

    send_email_if_necessary(sid)

    return HttpResponse()

@twilio_view
def transcription(request):
    twilio_request = decompose(request)
    sid = twilio_request.callsid

    with transaction.atomic():
        call = get_call_for_update(sid)
        call.transcription_received = True
        if twilio_request.transcriptionstatus == 'completed':
            call.transcription_successful = True
            call.transcription_text = twilio_request.transcriptiontext
        else:
            # Being a bit explicit about the fact that this field should be False here.
            call.transcription_successful = False
        call.save()

    send_email_if_necessary(sid)

    return HttpResponse()

@login_required
def index(request):
    context = {}
    return HttpResponse(render(request, 'callrouting/index.html', context))
