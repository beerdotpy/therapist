# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from models import Session


class SessionAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'date', 'start_time', 'duration', 'end_time', 'type', 'notes']
    list_filter = ['client_name']


admin.site.register(Session, SessionAdmin)

