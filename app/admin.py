# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from app.models import Session
from advanced_filters.admin import AdminAdvancedFiltersMixin


class ProfileAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):
    def start_time_format(self, obj):
        return obj.start_time.strftime("%H:%M:%S %p")

    def end_time_format(self, obj):
        return obj.end_time.strftime("%H:%M:%S %p")

    list_display = ['client_name', 'date', 'start_time_format', 'duration', 'end_time_format', 'type', 'notes']
    # specify which fields can be selected in the advanced filter
    # creation form
    advanced_filter_fields = (
        'client_name',
        'client_name'
    )

    list_filter = ['client_name']


admin.site.register(Session, ProfileAdmin)
