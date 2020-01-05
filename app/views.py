# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import csv
from models import Session
from django.shortcuts import render
from datetime import datetime
from django.forms.models import model_to_dict


@csrf_exempt
def parse_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        csv_reader = csv.reader(csv_file)
        name = ""
        duplicate = []
        overlap = []
        gap = []
        for row in csv_reader:
            if row[1]:
                name = row[1]
            if row[2] != '>' and row[0] != '' and row[0] != 'Initial':
                start_time = datetime.strptime(row[4], "%I:%M %p").time()
                end_time = datetime.strptime(row[6], "%I:%M %p").time()
                date = datetime.strptime((row[2] + " " + str(datetime.now().year)).replace(" ", "/"), "%a/%b/%d/%Y").date()
                # check duplicate
                result_1 = check_duplicate(name, row[0], date, start_time, row[5], end_time)
                if result_1:
                    duplicate.append(result_1)
                else:
                    result_2 = check_overlap(name, row[0], date, start_time, row[5], end_time)
                    if result_2:
                        overlap.append(result_2)
                    else:
                        result_3 = check_gap(name, row[0], date, start_time, row[5], end_time)
                        if result_3:
                            gap.append(result_3)
                        else:
                            session = Session()
                            session.client_initial = row[0]
                            session.notes = row[7]
                            session.duration = row[5]
                            session.type = row[3]
                            session.client_name = name
                            session.date = date
                            session.start_time = start_time
                            session.end_time = end_time
                            session.save()
        if len(duplicate) > 0 or len(overlap) > 0 or len(gap) > 0:
            return render(request, "home.html", {"duplicate": duplicate, 'overlap': overlap, 'gap': gap})
        else:
            return HttpResponse("Saved", 200)
    return render(request, "home.html")


def check_duplicate(name, client_initial, date, start_time, duration, end_time):
    result = Session.objects.filter(client_initial=client_initial,
                                    date=date,
                                    start_time=start_time,
                                    end_time=end_time)
    if result:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'error': 'Duplicate'}
        return data
    else:
        return None


def check_overlap(name, client_initial, date, start_time, duration, end_time):
    result = Session.objects.filter(client_initial=client_initial,
                                    date=date,
                                    start_time__lt=start_time,
                                    end_time__gt=start_time)
    if not result:
        result = Session.objects.filter(client_initial=client_initial,
                                        date=date,
                                        start_time__lt=end_time,
                                        end_time__gt=end_time)
    if result:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'error': 'Overlap'}
        return data
    else:
        return None


def check_gap(name, client_initial, date, start_time, duration, end_time):
    result = Session.objects.filter(client_initial=client_initial,
                                    date=date)
    for i in result:
        if i.start_time > start_time and not i.start_time == end_time:
            data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                    'duration': duration, 'end_time': end_time, 'error': 'Gap'}
            return data
        elif i.start_time < start_time and not i.end_time == start_time:
            data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                    'duration': duration, 'end_time': end_time, 'error': 'Gap'}
            return data
    return None
