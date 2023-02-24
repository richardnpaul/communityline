from django.contrib import admin
from solo.admin import SingletonModelAdmin
from callrouting.models import Shift, Volunteer, EmailState, UserGroup, Call

# Register your models here.

admin.site.register(Shift)
admin.site.register(Volunteer)
admin.site.register(EmailState, SingletonModelAdmin)
admin.site.register(UserGroup)
admin.site.register(Call)