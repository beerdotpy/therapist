# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from app.models import Session, Availability
from advanced_filters.admin import AdminAdvancedFiltersMixin


class ProfileAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):

    def start_time(self, obj):
        return obj.start_time.strftime("%H:%M %p")

    def end_time(self, obj):
        return obj.end_time.strftime("%H:%M %p")

    def date(self, obj):
        return obj.date.strftime("%a %b %d")

    def client(self, obj):
        return obj.client_name

    list_display = ['client', 'date', 'start_time', 'duration', 'end_time', 'type', 'notes',
                    'status', 'is_accepted', 'is_disputed']
    # specify which fields can be selected in the advanced filter
    # creation form
    advanced_filter_fields = (
        'client_name',
        'client_name',
        'status',
        'date',
    )

    list_filter = ['status', 'is_accepted', 'is_disputed', 'client_name', 'date']


admin.site.register(Session, ProfileAdmin)
