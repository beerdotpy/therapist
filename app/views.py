# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import csv
from models import Session
from django.shortcuts import render
import json


@csrf_exempt
def parse_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        csv_reader = csv.reader(csv_file)
        name = ""
        for row in csv_reader:
            if row[1]:
                name = row[1]
            if row[2] != '>' and row[0] != '':
                print row
                session = Session()
                session.client_initial = row[0]
                session.notes = row[7]
                session.duration = row[5]
                session.type = row[3]
                session.client_name = name
                session.start_date = row[2] + " " + row[4]
                session.end_date = row[2] + " " + row[6]
                session.save()
        return HttpResponse("Saved", 200)
    return render(request, "home.html")
