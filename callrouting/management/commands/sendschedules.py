# Standard Library Imports
import datetime
import logging
import sys

# Django Imports
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

# App Imports
from callrouting.models import EmailState, Shift, hour_labels


logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class Command(BaseCommand):
    help = "Emails tomorrow's volunteers information about their schedule"

    def add_arguments(self, parser):
        """Can add arguments here, but not needed so far for sending schedules."""

    def handle(self, *args, **options):
        logger.info('Schedule sending process beginning...')
        email_state = EmailState.get_solo()
        # Check if there's a send already in progress
        logger.info('Checking if email send process already in progress...')
        if email_state.in_progress:
            # If so, this is an error - exit and log
            logger.error('Email process already in progress')

        # Check whether emails have already been sent today
        sent_date = email_state.last_sent
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        # - If it's already today's date then we're done for the day
        if sent_date == today:
            logger.info("Today's (%s) emails already sent - exiting" % today)
            return
        # - If it's beyond today's date then something's badly wrong - exit with error
        if sent_date > today:
            raise CommandError("Sent date (%s) is greater than today's date (%s)" % (sent_date, today))
        # - If it's not yesterdays, then something is weird - e.g. maybe a day was skipped - log, but continue
        if sent_date < yesterday:
            logger.warn("Sent date (%s) is more than one day behind today (%s) - were some emails skipped?"
                        % (sent_date, today))

        # Log that the email process has been triggered
        logger.info('Starting schedule send process')

        # Mark the sending process as started
        email_state.in_progress = True
        email_state.save()

        # Get all shifts for tomorrow
        tomorrow_string = (today + datetime.timedelta(days=1)).strftime('%A')
        tomorrow_shifts = Shift.objects.filter(day__exact=tomorrow_string)

        # Log the list of shifts and volunteers, and whether they will receive email
        logger.info("Tomorrow's shifts:")
        for shift in tomorrow_shifts:
            send_emails = shift.volunteer.send_emails
            logger.info('- %s / send email: %s' % (shift, send_emails))

        # Create a list of emails - aggregate all shifts for each volunteer who
        # wants to receive mail
        volunteer_shifts = {}
        for shift in tomorrow_shifts:
            volunteer = shift.volunteer
            if shift.volunteer.send_emails:
                existing_shifts = volunteer_shifts.get(volunteer)
                if not existing_shifts:
                    existing_shifts = []
                    volunteer_shifts[volunteer] = existing_shifts
                existing_shifts.append(shift)

        for volunteer, shift_list in volunteer_shifts.items():
            print("Volunteer %s has %s" % (volunteer, ','.join(['%s' % s for s in shift_list])))

        # Send email to each volunteer who has it enabled - format the template and send
        # - Log the emails that actually get sent: one at a time
        # TRYING TO MAKE THE RENDERING BETTER  -SOME BAD SYNTAX HERE?
        for volunteer, shifts in volunteer_shifts.items():
            shift_list = [ {'start': hour_labels(s.start_time),
                            'end': hour_labels(shift.end_time)}
                            for s in shifts ]
            context = {
                'volunteer': volunteer,
                'shift_list': shift_list,
            }
            text = render_to_string('callrouting/shift_email.html', context)
            print(text)
        # Log that we're going to update the emails sent date
        # Update the emails sent date

        # Log that we're about to unset the in-progress flag, and un-set
        logger.info('Finishing email send process (unsetting in-progress flag)')
        email_state.in_progress = False
        email_state.save()

        # Log that we've completed the process
        logger.info('Email send process completed.')
