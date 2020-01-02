# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from app.models import Session
from advanced_filters.admin import AdminAdvancedFiltersMixin


class ProfileAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):
    list_display = ['client_name', 'date', 'start_time', 'duration', 'end_time', 'type', 'notes']
    # specify which fields can be selected in the advanced filter
    # creation form
    advanced_filter_fields = (
        'client_name',
        'client_name'
    )


admin.site.register(Session, ProfileAdmin)
