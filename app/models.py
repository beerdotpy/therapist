# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


class Session(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    client_initial = models.CharField(max_length=10)
    client_name = models.CharField(max_length=200)
    duration = models.CharField(max_length=50)
    start_date = models.CharField(max_length=200)
    end_date = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    notes = models.TextField()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.id = self.client_initial + "_" + self.start_date + "_" + self.end_date
        print self.id
        return super(Session, self).save()
