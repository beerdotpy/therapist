# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


class Session(models.Model):
    client_initial = models.CharField(max_length=10)
    client_name = models.CharField(max_length=200)
    duration = models.CharField(max_length=50)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    type = models.CharField(max_length=200)
    notes = models.TextField()
