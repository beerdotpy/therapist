# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
import csv
from models import Session, TempSession
from django.shortcuts import render
from datetime import datetime
import uuid
from django.http import HttpResponse
import json
from rest_framework.renderers import JSONRenderer
from serializers import SessionSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

from_email = 'contact@gmail.com'
to_email = ['sarthakmeh03@gmail.com', 'kkalaawy@gmail.com']


@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data['password'] == 'admin@2019':
            name = data['email'].split("@")[0]
            return HttpResponse(json.dumps({"status": "Authorized", "client_name": name}), status=200)
        else:
            return HttpResponse(json.dumps({"status": "UnAuthorized"}), status=401)


@csrf_exempt
def get_sessions(request):
    if request.method == 'GET':
        current_date = datetime.today().date()
        sessions = Session.objects.filter(client_name__icontains=request.GET['client_name'],
                                          is_accepted=request.GET['is_accepted'],
                                          date__gte=current_date).exclude(status__in=['Cancellation',
                                                                                      'Late Cancellation'])
        serializer = SessionSerializer(sessions, many=True)
        return HttpResponse(JSONRenderer().render(serializer.data), status=200)


@csrf_exempt
def get_timesheet(request):
    if request.method == 'GET':
        current_date = datetime.today().date()
        # TODO - Change month lte to only lt
        sessions = Session.objects.filter(client_name__icontains=request.GET['client_name'],
                                          date__month__lte=current_date.month).exclude(status='Cancellation')
        serializer = SessionSerializer(sessions, many=True)
        return HttpResponse(JSONRenderer().render(serializer.data), status=200)


@csrf_exempt
def update_sessions(request):
    if request.method == 'GET':
        if request.GET['action'] == 'Accept':
            try:
                session = Session.objects.get(client_name=request.GET['client_name'],
                                              start_time=request.GET['start_time'],
                                              end_time=request.GET['end_time'], date=request.GET['date'])
                session.is_accepted = True
                session.save()
            except ObjectDoesNotExist:
                return HttpResponse(json.dumps({'status': 'Not Accepted'}), status=400)
            return HttpResponse(json.dumps({'status': 'Accepted'}), status=200)
        elif request.GET['action'] == 'Edit':
            session = Session.objects.get(client_name=request.GET['client_name'],
                                          start_time=request.GET['start_time'],
                                          end_time=request.GET['end_time'], date=request.GET['date'])
            session.status = 'Request Sent'
            session.save()
            message = request.GET['client_name'] + " has requested modification in the below session<br>" \
                      + "Start Time - " + request.GET['start_time'] + "<br>End Time - " + request.GET['end_time'] + \
                      "<br>Date - " + request.GET['date'] + "<br><br>NEW SESSION REQUESTED: <br>" + request.GET[
                          'message']
            send_mail(request.GET['client_name'] + " has requested an edit in session",
                      '',
                      from_email,
                      to_email,
                      html_message=message)
            return HttpResponse(json.dumps({'status': 'Updated'}), status=200)
        elif request.GET['action'] == 'Cancel':
            session = Session.objects.get(client_name=request.GET['client_name'],
                                          start_time=request.GET['start_time'],
                                          end_time=request.GET['end_time'], date=request.GET['date'])
            if request.GET['message'] == 'true':
                message = request.GET[
                              'client_name'] + " has requested <b>late cancellation</b> in the below session<br>" \
                          + "<br>Start Time - " + request.GET['start_time'] + "<br>End Time - " + request.GET[
                              'end_time'] + \
                          "<br>Date - " + request.GET['date']
                session.status = 'Late Cancellation'
                session.save()
            else:
                session.status = 'Request Sent'
                session.save()
                message = request.GET['client_name'] + " has requested cancellation in the below session<br>" \
                          + "<br>Start Time - " + request.GET['start_time'] + "<br>End Time - " + request.GET[
                              'end_time'] + \
                          "<br>Date - " + request.GET['date']
            send_mail(request.GET['client_name'] + " has cancelled a session",
                      '',
                      from_email,
                      to_email,
                      html_message=message)
            return HttpResponse(json.dumps({'status': 'Cancelled'}), status=200)
        elif request.GET['action'] == 'RaiseQuery':
            try:
                session = Session.objects.get(client_name=request.GET['client_name'],
                                              start_time=request.GET['start_time'],
                                              end_time=request.GET['end_time'], date=request.GET['date'])
            except ObjectDoesNotExist:
                return HttpResponse(json.dumps({'status': 'Not Found'}), status=400)
            message = request.GET['client_name'] + " has raised concern for the below session in the Timesheet<br>" \
                      + "<br>Start Time - " + request.GET['start_time'] + "<br>End Time - " + request.GET['end_time'] + \
                      "<br>Date - " + request.GET['date'] + "<br>Query: " + request.GET['message']
            send_mail(request.GET['client_name'] + " has raised a concern in the Timesheet",
                      '',
                      from_email,
                      to_email,
                      html_message=message)
            return HttpResponse(json.dumps({'status': 'Concerned Raised'}), status=200)
        elif request.GET['action'] == 'AcceptAll':
            send_mail(request.GET['client_name'] + " has accepted the Timesheet",
                      '',
                      from_email,
                      to_email)
        return HttpResponse(json.dumps({'status': 'Action not available'}), status=200)


@csrf_exempt
def parse_csv(request):
    if request.method == 'POST':
        if request.POST['button'] == 'Upload':
            csv_file = request.FILES['csv_file']
            result_list = check_csv(csv_file)
            return render(request, "home.html", {"result": result_list, "button_type": "Review", "file": csv_file})
        elif request.POST['button'] == 'Review':
            result_list = check_records(request.POST['data'])
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
        if row[2] != '>' and row[0] != '' and row[2] != 'Date':
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


def check_records(filename):
    records = TempSession.objects.filter(filename=filename)
    result_list = []
    name = ""
    id = uuid.uuid1(4)
    for row in list(records):
        if name == "" or name != row.client_name:
            # records which are present in the admin panel but have been removed from csv
            for i in Session.objects.filter(client_name=name, date__month__gte=row.date.month).exclude(updated_at=id):
                session = TempSession()
                session.client_initial = i.client_initial
                session.notes = i.notes
                session.duration = i.duration
                session.type = i.type
                session.client_name = i.client_name
                session.date = i.date
                session.start_time = i.start_time
                session.end_time = i.end_time
                session.filename = filename
                session.error = "Cancellation"
                session.save()
                result_list.append(session)
            name = row.client_name

        result_1 = check_duplicate(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                   row.end_time, row.notes, row.type, False, id)
        if result_1:
            row.error = result_1['error']
            row.save()
        else:
            result_2 = check_overlap(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                     row.end_time, row.notes, row.type, False, id)
            if result_2:
                row.error = result_2[0]['error']
                row.save()
                result_list.append(result_2[0])
                for i in result_2[1:]:
                    session = TempSession()
                    session.client_initial = i['client_initial']
                    session.notes = i['notes']
                    session.duration = i['duration']
                    session.type = i['type']
                    session.client_name = i['client_name']
                    session.date = i['date']
                    session.start_time = i['start_time']
                    session.end_time = i['end_time']
                    session.filename = filename
                    session.error = i['error']
                    session.save()
                    result_list.append(i)
            else:
                result_3 = check_gap(row.client_name, row.client_initial, row.date, row.start_time, row.duration,
                                     row.end_time, row.notes, row.type, False, id)
                if result_3:
                    row.error = result_3[0]['error']
                    row.save()
                    result_list.append(result_3[0])
                    for i in result_3[1:]:
                        session = TempSession()
                        session.client_initial = i['client_initial']
                        session.notes = i['notes']
                        session.duration = i['duration']
                        session.type = i['type']
                        session.client_name = i['client_name']
                        session.date = i['date']
                        session.start_time = i['start_time']
                        session.end_time = i['end_time']
                        session.filename = filename
                        session.error = i['error']
                        session.save()
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
        if i.error == 'No Change':
            Session.objects.filter(client_name=i.client_name, date=i.date, start_time=i.start_time,
                                   end_time=i.end_time, duration=i.duration).update(status=i.error)
            pass
        elif i.error == 'Cancellation':
            session = Session.objects.filter(client_name=i.client_name, date=i.date, start_time=i.start_time,
                                             end_time=i.end_time, duration=i.duration)
            if session[0].status != 'Late Cancellation':
                session.update(status=i.error)
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
            Session.objects.create(client_initial=i.client_initial, client_name=i.client_name, date=i.date,
                                   start_time=i.start_time, end_time=i.end_time, type=i.type, notes=i.notes,
                                   duration=i.duration, status=i.error).save()
    TempSession.objects.all().delete()


def check_duplicate(name, client_initial, date, start_time, duration, end_time, notes, types, temp, id=None):
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
        result[0].updated_at = id
        result[0].save()
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'No Change'}
        return data
    else:
        return None


def check_overlap(name, client_initial, date, start_time, duration, end_time, notes, types, temp, id=None):
    result = None
    found_2 = None
    found_1 = None
    if temp:
        result = TempSession.objects.filter(client_initial=client_initial,
                                            date=date,
                                            start_time__lte=start_time,
                                            end_time__gt=start_time)
        if not result:
            result = TempSession.objects.filter(client_initial=client_initial,
                                                date=date,
                                                start_time__lt=end_time,
                                                end_time__gt=end_time)

    else:
        found_1 = Session.objects.filter(client_initial=client_initial,
                                         date=date,
                                         start_time__lt=start_time,
                                         end_time__gt=start_time)
        found_2 = Session.objects.filter(client_initial=client_initial,
                                         date=date,
                                         start_time__lt=end_time,
                                         end_time__gt=end_time)

    if result and temp:
        data = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Overlap'}
        return data
    elif found_1 or found_2 and not temp:
        r_list = []
        data_1 = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                  'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Update'}
        r_list.append(data_1)
        if found_1:
            found_1[0].updated_at = id
            found_1[0].save()
            data_2 = {'client_name': found_1[0].client_name, 'client_initial': found_1[0].client_initial,
                      'date': found_1[0].date, 'start_time': found_1[0].start_time, 'duration': found_1[0].duration,
                      'end_time': found_1[0].end_time, 'notes': found_1[0].notes, 'type': found_1[0].type,
                      'error': 'Cancellation'}
            r_list.append(data_2)
        if found_2:
            found_2[0].updated_at = id
            found_2[0].save()
            data_3 = {'client_name': found_2[0].client_name, 'client_initial': found_2[0].client_initial,
                      'date': found_2[0].date, 'start_time': found_2[0].start_time, 'duration': found_2[0].duration,
                      'end_time': found_2[0].end_time, 'notes': found_2[0].notes, 'type': found_2[0].type,
                      'error': 'Cancellation'}
            r_list.append(data_3)
        return r_list
    else:
        return None


def check_gap(name, client_initial, date, start_time, duration, end_time, notes, types, temp, id=None):
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
        r_list = []
        data_1 = {'client_name': name, 'client_initial': client_initial, 'date': date, 'start_time': start_time,
                  'duration': duration, 'end_time': end_time, 'notes': notes, 'type': types, 'error': 'Update'}
        r_list.append(data_1)
        for i in Session.objects.filter(client_initial=client_initial, date=date):
            i.updated_at = id
            i.save()
            data = {'client_name': i.client_name, 'client_initial': i.client_initial,
                    'date': i.date, 'start_time': i.start_time, 'duration': i.duration,
                    'end_time': i.end_time, 'notes': i.notes, 'type': i.type, 'error': 'Cancellation'}
            r_list.append(data)
        return r_list
    else:
        return None
