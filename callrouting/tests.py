# Django Imports
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Local Imports
from .models import Shift, UserGroup, Volunteer


# Create your tests here.


class ShiftTests(TestCase):
    pass

class VolunteerTests(TestCase):
    pass

def create_one_user_group():
    name = 'Test Group 1 (voicemail default)'
    incoming_number = '+441522123456'
    greeting = 'This is the test group. Please hold'
    default_action = UserGroup.DefaultAction.VOICEMAIL
    voicemail_email = 'testgroup1@domain.local'
    voicemail_greeting = 'This is the test group voicemail'
    return UserGroup.objects.create(name=name, incoming_number=incoming_number, greeting=greeting,
        default_action=default_action, voicemail_email=voicemail_email,
        voicemail_greeting=voicemail_greeting)


def create_shift_with_volunteer(name, number, day, start_time, end_time,
                                user_group, email):
    v = Volunteer.objects.create(name=name, number=number, user_group=user_group,
        email=email)
    return Shift.objects.create(volunteer=v, day=day, start_time=start_time, end_time=end_time,
        user_group=user_group)

class VolunteersViewNoShiftTests(TestCase):
    @classmethod
    def setUpTestData(self):
        User = get_user_model()
        User.objects.create_user('temporary', 'temporary@domain.local', 'temporary')
        self.user_group = create_one_user_group()

    def test_no_shifts(self):
        """
        Ensure that there are no volunteers reported when there are no
        volunteers in the database.
        """
        ug_id = self.user_group.id
        self.client.login(username='temporary', password='temporary')
        for day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'):
            for time in range(6, 23):
                with self.subTest(day=day, time=time):
                    response = self.client.get(reverse('callrouting:volunteers', args=(ug_id, day, time)))
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, 'No volunteers')
                    self.assertQuerysetEqual(response.context['shifts'], [])

class VolunteersViewOneShiftTests(TestCase):
    @classmethod
    def setUpTestData(self):
        User = get_user_model()
        User.objects.create_user('temporary', 'temporary@domain.local', 'temporary')
        self.user_group = create_one_user_group()
        shift = create_shift_with_volunteer('Steve Smith', '+441234999888', 'Monday', 8, 11,
            self.user_group, 'stevesmith@domain.local')

    def setUp(self):
        self.client.login(username='temporary', password='temporary')

    def test_one_shift_volunteer_off(self):
        """
        Ensure that there are no volunteers reported at times when no volunteer is available.
        """
        ug_id = self.user_group.id
        for day in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'):
            for time in range(6, 23):
                if day == 'Monday' and 8 <= time < 11:
                    continue
                with self.subTest(day=day, time=time):
                    response = self.client.get(reverse('callrouting:volunteers', args=(ug_id, day, time)))
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, 'No volunteers')
                    self.assertQuerysetEqual(response.context['shifts'], [])

    def test_one_shift_volunteer_on(self):
        """
        Ensure that the volunteer available is reported for the given day
        and times for which they're available.
        """
        day = 'Monday'
        ug_id = self.user_group.id
        for time in range(8,11):
            response = self.client.get(reverse('callrouting:volunteers', args=(ug_id, day, time)))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '+441234999888')
            self.assertContains(response, 'Steve Smith')
            shifts = response.context['shifts']
            volunteer = Volunteer.objects.get(name="Steve Smith")
            expected_shifts = [Shift.objects.get(
                volunteer = volunteer.id,
                user_group = ug_id,
                day = day)]
            self.assertQuerysetEqual(shifts, expected_shifts)

class UnfinishedTests(TestCase):
    def test_two_shifts_nonoverlapping(self):
        """
        Test that the correct volunteer is shown when there
        are two shifts that don't overlap.

        At all other times, no volunteer should be reported.
        """
        # FIXME: implement

    def test_two_shifts_overlapping(self):
        """
        Test that the correct volunteer(s) are shown when there
        are two shifts that overlap. In some cases one volunteer
        will be listed - in others, when the shifts overlap, there
        will be two.

        At all other times, no volunteer should be reported.
        """
        # FIXME: implement

class ViewsRequiringLoginTests(TestCase):
    @classmethod
    def setUpTestData(self):
        # Bare minimum needed to get the view to function
        User = get_user_model()
        User.objects.create_user('temporary', 'temporary@domain.local', 'temporary')
        self.user_group = create_one_user_group()

    def test_volunteers_view_needs_login(self):
        # A valid user group and any old day and time will do for this test.
        ug_id = self.user_group.id
        day = 'Monday'
        time = 8
        response = self.client.get(reverse('callrouting:volunteers', args=(ug_id, day, time)))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
