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
            return render(request, "home.html", {"result": result_list, "button_type": "Submit"})
        elif request.POST['button'] == 'Submit':
            save_records(list(TempSession.objects.all()))
            return render(request, "home.html", {"button_type": "Saved"})
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
            result_1 = check_duplicate(name, row[0], date, start_time, row[5], end_time, row[7], row[3], True)
            if result_1:
                result_list.append(result_1)
            else:
                result_2 = check_overlap(name, row[0], date, start_time, row[5], end_time, row[7], row[3], True)
                if result_2:
                    result_list.append(result_2)
                else:
                    result_3 = check_gap(name, row[0], date, start_time, row[5], end_time, row[7], row[3], True)
                    if result_3:
                        result_list.append(result_3)
                    else:
                        data = {'client_name': name, 'client_initial': row[0], 'date': date,
                                'start_time': start_time, 'duration': row[5], 'end_time': end_time,
                                'notes': row[7], 'type': row[3], 'error': 'OK'}
                        result_list.append(data)
            session.save()
    return result_list


def check_records(records):
    result_list = []
    for row in list(records):
        result_1 = check_duplicate(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                   row.end_time, row.notes, row.type, False)
        if result_1:
            row.error = result_1['error']
            row.save()
            result_list.append(result_1)
        else:
            result_2 = check_overlap(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                     row.end_time, row.notes, row.type, False)
            if result_2:
                row.error = result_list[0]['error']
                row.save()
                for i in result_2:
                    result_list.append(i)
            else:
                result_3 = check_gap(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                     row.end_time, row.notes, row.type, False)
                if result_3:
                    row.error = result_list[0]['error']
                    row.save()
                    for i in result_3:
                        result_list.append(i)
                else:
                    row.error = 'NEW'
                    row.save()
                    data = {'client_name': row.client_name, 'client_initial': row.client_initial, 'date': row.date,
                            'start_time': row.start_time, 'duration': row.duration, 'end_time': row.end_time,
                            'notes': row.notes, 'type': row.type, 'error': 'NEW'}
                    result_list.append(data)
    return result_list


def save_records(results):
    for i in results:
        if i.error == 'Already Exists':
            pass
        elif i.error == 'Cancellation':
            pass
        elif i.error == 'NEW':
            session = Session()
            session.client_initial = i.client_initial
            session.client_name = i.client_name
            session.duration = i.duration
            session.date = i.date
            session.start_time = i.start_time
            session.end_time = i.end_time
            session.type = i.type
            session.notes = i.notes
            session.save()
        elif i.error == 'Update':
            Session.objects.filter(client_name=i.client_name, date=i.date).update(
                start_time=i.start_time,
                end_time=i.end_time,
                type=i.type,
                notes=i.notes,
                duration=i.duration)
    TempSession.objects.all().delete()


def check_duplicate(name, client_initial, date, start_time, duration, end_time, notes, types, temp):
    if temp:
        result = TempSession.objects.filter(client_initial=client_initial,
                                            date=date,
                                            start_time=start_time,
                                            end_time=end_time,
                                            notes=notes,
                                            type=types)
    else:
        result = Session.objects.filter(client_initial=client_initial,
                                        date=date,
                                        start_time=start_time,
                                        end_time=end_time,
                                        notes=notes,
                                        type=types)

    if result and temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Duplicate'}
        return data
    elif result and not temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Already Exists'}
        return data
    else:
        return None


def check_overlap(name, client_initial, date, start_time, duration, end_time, notes, types, temp):
    if temp:
        result = TempSession.objects.filter(client_initial=client_initial,
                                            date=date,
                                            start_time__lt=start_time,
                                            end_time__gt=start_time,
                                            notes=notes,
                                            type=types)
    else:
        result = Session.objects.filter(client_initial=client_initial,
                                        date=date,
                                        start_time__lt=start_time,
                                        end_time__gt=start_time,
                                        notes=notes,
                                        type=types)
    if not result:
        if temp:
            result = TempSession.objects.filter(client_initial=client_initial,
                                                date=date,
                                                start_time__lt=end_time,
                                                end_time__gt=end_time,
                                                notes=notes,
                                                type=types)
        else:
            result = Session.objects.filter(client_initial=client_initial,
                                            date=date,
                                            start_time__lt=end_time,
                                            end_time__gt=end_time,
                                            notes=notes,
                                            type=types)

    if result and temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Overlap'}
        return data
    elif result and not temp:
        data_1 = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                  'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Update'}
        data_2 = {'client_name': result[0].client_name, 'client_initial': result[0].client_initial,
                  'date': result[0].date, 'start_time': result[0].start_time, 'duration': result[0].duration,
                  'end_time': result[0].end_time, 'notes': notes, 'type': types, 'error': 'Cancellation'}
        return [data_1, data_2]
    else:
        return None


def check_gap(name, client_initial, date, start_time, duration, end_time, notes, types, temp):
    if temp:
        if len(TempSession.objects.filter(client_initial=client_initial, date=date)) > 0:
            result = TempSession.objects.filter(client_initial=client_initial, date=date,
                                                start_time__gt=start_time, start_time=end_time)
            if not result:
                result = TempSession.objects.filter(client_initial=client_initial, date=date,
                                                    start_time__lt=start_time, end_time=start_time)
        else:
            return None
    else:
        if len(Session.objects.filter(client_initial=client_initial, date=date)) > 0:
            result = Session.objects.filter(client_initial=client_initial, date=date,
                                            start_time__gt=start_time, start_time=end_time)
            if not result:
                result = Session.objects.filter(client_initial=client_initial, date=date,
                                                start_time__lt=start_time, end_time=start_time)
        else:
            return None

    if not result and temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Gap'}
        return data
    elif not result and not temp:
        data_1 = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                  'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Update'}
        latest = Session.objects.filter(client_initial=client_initial, date=date)[0]
        data_2 = {'client_name': latest.client_name, 'client_initial': latest.client_initial,
                  'date': latest.date, 'start_time': latest.start_time, 'duration': latest.duration,
                  'end_time': latest.end_time, 'notes': latest.notes, 'type': latest.type, 'error': 'Cancellation'}
        return [data_1, data_2]
    else:
        return None
