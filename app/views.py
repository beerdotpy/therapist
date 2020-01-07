# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
import csv
from models import Session, TempSession
from django.shortcuts import render
from datetime import datetime


@csrf_exempt
def parse_csv(request):
    if request.method == 'POST':
        if request.POST['button'] == 'Upload':
            csv_file = request.FILES['csv_file']
            result_list = check_csv(csv_file)
            return render(request, "home.html", {"result": result_list, "button_type": "Review", "file": csv_file})
        elif request.POST['button'] == 'Review':
            result_list = check_records(TempSession.objects.filter(filename=request.POST['data']))
            return render(request, "home.html", {"result": result_list, "button_type": "Review"})
    return render(request, "home.html", {"button_type": "Upload"})


def check_csv(csv_file):
    TempSession.objects.all().delete()
    csv_reader = csv.reader(csv_file)
    name = ""
    result_list = []
    for row in csv_reader:
        if row[1]:
            name = row[1]
        if row[2] != '>' and row[0] != '' and row[0] != 'Initial':
            start_time = datetime.strptime(row[4], "%I:%M %p").time()
            end_time = datetime.strptime(row[6], "%I:%M %p").time()
            date = datetime.strptime((row[2] + " " + str(datetime.now().year)).replace(" ", "/"), "%a/%b/%d/%Y").date()
            session = TempSession()
            session.client_initial = row[0]
            session.notes = row[7]
            session.duration = row[5]
            session.type = row[3]
            session.client_name = name
            session.date = date
            session.start_time = start_time
            session.end_time = end_time
            session.filename = csv_file
            # check duplicate
            result_1 = check_duplicate(name, row[0], date, start_time, row[5], end_time, True)
            if result_1:
                result_list.append(result_1)
            else:
                result_2 = check_overlap(name, row[0], date, start_time, row[5], end_time, True)
                if result_2:
                    result_list.append(result_2)
                else:
                    result_3 = check_gap(name, row[0], date, start_time, row[5], end_time, True)
                    if result_3:
                        result_list.append(result_3)
                    else:
                        data = {'client_name': name, 'client_initial': row[0], 'date': date,
                                'start_time': start_time, 'duration': row[5], 'end_time': end_time, 'error': 'OK'}
                        result_list.append(data)
            session.save()
    return result_list


def check_records(records):
    result_list = []
    for row in list(records):
        result_1 = check_duplicate(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                   row.end_time, False)
        if result_1:
            result_list.append(result_1)
        else:
            result_2 = check_overlap(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                     row.end_time, False)
            if result_2:
                for i in result_2:
                    result_list.append(i)
            else:
                result_3 = check_gap(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                     row.end_time, False)
                if result_3:
                    for i in result_3:
                        result_list.append(i)
                else:
                    data = {'client_name': row.client_name, 'client_initial': row.client_initial, 'date': row.date,
                            'start_time': row.start_time, 'duration': row.duration, 'end_time': row.end_time, 'error': 'NEW'}
                    result_list.append(data)
    return result_list


def check_duplicate(name, client_initial, date, start_time, duration, end_time, temp):
    if temp:
        result = TempSession.objects.filter(client_initial=client_initial,
                                            date=date,
                                            start_time=start_time,
                                            end_time=end_time)
    else:
        result = Session.objects.filter(client_initial=client_initial,
                                        date=date,
                                        start_time=start_time,
                                        end_time=end_time)

    if result and temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'error': 'Duplicate'}
        return data
    elif result and not temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'error': 'Already Exists'}
        return data
    else:
        return None


def check_overlap(name, client_initial, date, start_time, duration, end_time, temp):
    if temp:
        result = TempSession.objects.filter(client_initial=client_initial,
                                            date=date,
                                            start_time__lt=start_time,
                                            end_time__gt=start_time)
    else:
        result = Session.objects.filter(client_initial=client_initial,
                                        date=date,
                                        start_time__lt=start_time,
                                        end_time__gt=start_time)

    if not result:
        result = Session.objects.filter(client_initial=client_initial,
                                        date=date,
                                        start_time__lt=end_time,
                                        end_time__gt=end_time)
    if result and temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'error': 'Overlap'}
        return data
    elif result and not temp:
        data_1 = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                  'duration': duration, 'end_time': end_time, 'error': 'Update'}
        data_2 = {'client_name': result[0].client_name, 'client_initial': result[0].client_initial, 'date': result[0].date,
                  'start_time': result[0].start_time, 'duration': result[0].duration, 'end_time': result[0].end_time,
                  'error': 'Cancellation'}
        return [data_1, data_2]
    else:
        return None


def check_gap(name, client_initial, date, start_time, duration, end_time, temp):
    if temp:
        result = TempSession.objects.filter(client_initial=client_initial, date=date)
    else:
        result = Session.objects.filter(client_initial=client_initial, date=date)
    for i in result:
        if i.start_time > start_time and not i.start_time == end_time:
            if temp:
                data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                        'duration': duration, 'end_time': end_time, 'error': 'Gap'}
                return data
            else:
                data_1 = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                          'duration': duration, 'end_time': end_time, 'error': 'Update'}
                data_2 = {'client_name': i.client_name, 'client_initial': i.client_initial,
                          'date': i.date, 'start_time': i.start_time, 'duration': i.duration,
                          'end_time': i.end_time, 'error': 'Removed'}
                return [data_1, data_2]
        elif i.start_time < start_time and not i.end_time == start_time:
            if temp:
                data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                        'duration': duration, 'end_time': end_time, 'error': 'Gap'}
                return data
            else:
                data_1 = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                          'duration': duration, 'end_time': end_time, 'error': 'Update'}
                data_2 = {'client_name': i.client_name, 'client_initial': i.client_initial,
                          'date': i.date, 'start_time': i.start_time, 'duration': i.duration,
                          'end_time': i.end_time, 'error': 'Removed'}
                return [data_1, data_2]
    return None
