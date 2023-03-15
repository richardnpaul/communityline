# Community line

A system developed in a hurry in March 2020 to automate the routing of telephone
calls to volunteer workers.

- Multiple volunteer groups are supported.
- Calls are handled by Twilio - the system allows definition of who the call
  will route to at a given hour.
- Voicemail service can also be provided, with the recording and transcript
  emailed to a specified email address for a given volunteer group. Sendgrid is
  used for sending mails.
- Batch email sending to volunteers for the next day, to remind them they have a
  shift on the phone.
- The system ran on a free Heroku dyno, which is no longer available.

## Limitations

May not be usable in its exact current form, but is open-sourced in case it is
of interest (or amusement!) for someone. Specific limitations:

- Not much documentation.
- Not very comprehensive testing.
- Some of the code is not very well-written for readability / maintainability.
  The main aim was to write the code in such a way as to minimise the chance of
  making a mistake since I didn't have many tests or much time.
- I had to anonymise / edit some hardcoded details (email addresses etc.) when
  preparing for open-source. This may not have resulted in consistent names in
  some places.

# Notes

The following sections are a verbatim reproduction of notes I kept for myself
whilst running and developing the system. They have not been edited for general
readability yet.

## Development

- `python manage.py makemigrations` after modifying models
- `python manage.py migrate` after making migrations

## Ops

- Backups:
  - `heroku pg:backups:capture --app communityline` to back up the database
  - `heroku pg:backups --app communityline` to see backups
  - `heroku pg:backups:url <backup number> --app communityline` to see backup URL to download
  - See docs for more (link below)
- Change Python version by editing runtime.txt
- Twilio Debugger: https://www.twilio.com/console/debugger
- Deploying to Heroku:
  - `git push heroku master`
  - The deploy runs the migrations automatically

## Testing

### General preparation / running

- Open up anaconda powershell prompt
- Activate communityline environment
- Source env_vars.ps1: `. .\env_vars.ps1`
- Run `heroku local web -f Procfile.windows`

### Interactively with Postman

- Collection of queries exported into communityline-other
- Call handle URL to use: http://localhost:5000/callrouting/handle
  - Need to create a POST request with the `To` field populated with the called number
- There are postman saved queries for the recording and transcription hooks too.
  - These need the CallSid which must be "CA..." 34 chars and unique
  - Plus recording URL or transcription status and text as appropriate

### Exploration through the web interface

- Check volunteer at time: http://localhost:5000/callrouting/volunteers/<group id>/<day>/<time>
  - E.g. https://communityline.herokuapp.com/callrouting/volunteers/1/Monday/17
- Fire up ngrok:
  - `ngrok http 5000` in `C:\Grahamroot\communityline-other`.
  - Copy / paste HTTPS URL into Twilio Webhook URL with `/callrouting/handle` appended

### Automated testing

- Run with `python manage.py test <test spec>`
- e.g. `python manage.py test callrouting.tests.VolunteersViewTests.test_no_shifts`

## Resources:

- Getting started on Heroku with Python: https://devcenter.heroku.com/articles/getting-started-with-python
- Getting started sample code: https://github.com/heroku/python-getting-started
- Twilio call forwarding with flask example: https://www.twilio.com/docs/voice/tutorials/call-forwarding-python-flask
- Twilio Programmable Voice Python quickstart (info on using ngrok): https://www.twilio.com/docs/voice/quickstart/python#respond-to-incoming-calls-with-twilio
- TwiML docs (explains the responses and requests): https://www.twilio.com/docs/voice/twiml
  - TwiML recording docs: https://www.twilio.com/docs/voice/twiml/record
  - Getting started with Recording Status Callbacks: https://support.twilio.com/hc/en-us/articles/360014251313-Getting-Started-with-Recording-Status-Callbacks
  - Recording incoming Twilio Voice calls: https://support.twilio.com/hc/en-us/articles/360010317333-Recording-Incoming-Twilio-Voice-Calls
- Django tutorial: https://docs.djangoproject.com/en/3.1/intro/tutorial01/
- Mozilla LocalLibrary tutorial: https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django
  - Testing: https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Testing
- Django-twilio docs: https://django-twilio.readthedocs.io/en/latest/
- Deploying Python and Django apps on Heroku: https://devcenter.heroku.com/articles/deploying-python
- Heroku database backups: https://devcenter.heroku.com/articles/heroku-postgres-backups
- Heroku specifying a Python version: https://devcenter.heroku.com/articles/python-runtimes
- Sendgrid - Sending SMTP email with Django: https://sendgrid.com/docs/for-developers/sending-email/django/
- HTML validator: https://validator.w3.org/
