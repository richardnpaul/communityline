# Django Imports
from django.contrib import admin

# 3rd Party Imports
from solo.admin import SingletonModelAdmin

# App Imports
from callrouting.models import Call, EmailState, Shift, UserGroup, Volunteer


# Register your models here.

admin.site.register(Shift)
admin.site.register(Volunteer)
admin.site.register(EmailState, SingletonModelAdmin)
admin.site.register(UserGroup)
admin.site.register(Call)
