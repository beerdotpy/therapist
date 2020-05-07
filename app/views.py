# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
from models import Session, TempSession, Timesheet, Availability, User, StatHoliday
from django.shortcuts import render
from datetime import datetime
import uuid
from django.http import HttpResponse
import json
from rest_framework.renderers import JSONRenderer
from serializers import SessionSerializer, AvailabilitySerializer
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, EmailMessage
import csv
import os
from calendar import monthrange

from_email = 'contact@gmail.com'
to_email = ['sarthakmeh03@gmail.com', 'kkalaawy@gmail.com']
admin_pass = 'adminflc@2020'


@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            user = User.objects.get(email__iexact=data['email'])
        except ObjectDoesNotExist:
            if "adminflc.com" in data['email'] and data['password'] == admin_pass:
                username = data['email'].split('@')[0]
                return HttpResponse(json.dumps({"status": "Authorized", "client_name": username}), status=200)
            return HttpResponse(json.dumps({"status": "UnAuthorized"}), status=401)
        if data['password'] == user.password:
            return HttpResponse(json.dumps({"status": "Authorized", "client_name": user.name}), status=200)
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
        if int(request.GET['month']) == -1:
            dates = Session.objects.filter(client_name__icontains=request.GET['client_name']).dates('date', 'month', order="DESC")
            months = []
            for d in dates:
                if datetime.today().date() > d and datetime.today().date().month != d.month:
                    months.append(d.month)
            latest_month = -1
            if datetime.today().date().day > 5:
                if len(months) >= 1:
                    latest_month = months[0]
            else:
                if len(months) >= 2:
                    latest_month = months[1]
            sessions = Session.objects.filter(client_name__icontains=request.GET['client_name'],
                                              date__month=latest_month).exclude(status='Cancellation')
            try:
                timesheet = Timesheet.objects.get(client_name__icontains=request.GET['client_name'],
                                                  month=latest_month)
                is_accepted = timesheet.is_accepted
            except ObjectDoesNotExist:
                is_accepted = False
            serializer = SessionSerializer(sessions, many=True)
            response = {'status': is_accepted, 'sessions': serializer.data, 'archive_months': months}
            return HttpResponse(JSONRenderer().render(response), status=200)
        else:
            sessions = Session.objects.filter(client_name__icontains=request.GET['client_name'],
                                              date__month=int(request.GET['month']) + 1).exclude(status='Cancellation')
            try:
                timesheet = Timesheet.objects.get(client_name__icontains=request.GET['client_name'],
                                                  month=int(request.GET['month']) + 1)
                is_accepted = timesheet.is_accepted
            except ObjectDoesNotExist:
                is_accepted = False
            serializer = SessionSerializer(sessions, many=True)
            response = {'status': is_accepted, 'sessions': serializer.data}
            return HttpResponse(JSONRenderer().render(response), status=200)


@csrf_exempt
def get_stat_holidays(request):
    if request.method == 'GET':
        holidays = StatHoliday.objects.filter(date__month=datetime.today().month+1)
        days = []
        for i in holidays:
            days.append(i.date.day)
        return HttpResponse(JSONRenderer().render(days), status=200)


@csrf_exempt
def save_availability(request):
    if request.method == 'POST':
        data = eval(request.body)
        # Get total days for that particular month
        total_days = monthrange(datetime.today().year, int(data[str(41)]) + 1)[1]
        d = [['X' for i in range(49)] for j in range(total_days+1)]
        d[0][0] = data[str(40)]
        # First row of matrix will contain time slots
        for i in range(1):
            min = 8
            sec = 00
            for j in range(1, 49):
                d[i][j] = str(min) + ":" + str(sec)
                if sec == 45:
                    min += 1
                    sec = 00
                else:
                    sec += 15
        # 2nd row till last row will contain X where time is blocked and empty cell where time is allocated
        for j in range(1, total_days + 1):
            d[j][0] = str(j) + "/02/20"
            if data[str(j)] != 'X':
                start_time = data[str(j)].split(";")[0]
                end_time = data[str(j)].split(";")[1]
                start_hr = int(start_time.split(":")[0])
                start_min = start_time.split(":")[1]
                end_hr = int(end_time.split(":")[0])
                end_min = end_time.split(":")[1]
                start_pos = (start_hr - 8 + 3 * (start_hr-8)) + 1
                if start_min == '15':
                    start_pos += 1
                elif start_min == '30':
                    start_pos += 2
                elif start_min == '45':
                    start_pos += 3
                end_pos = (end_hr - 8 + 3 * (end_hr - 8)) + 1
                if end_min == '15':
                    end_pos += 1
                elif end_min == '30':
                    end_pos += 2
                elif end_min == '45':
                    end_pos += 3
                for i in range(start_pos, end_pos+1):
                    d[j][i] = ' '
        Availability(client_name=data[str(40)], month=int(data[str(41)]) + 1, availability=data).save()
        output_file = os.getcwd() + '/templates/availability.csv'
        with open(output_file, 'w') as file:
            writer = csv.writer(file)
            # Gives the header name row into csv
            writer.writerow(d[0])
            # Data add in csv file
            for i in d[1:]:
                writer.writerow(i)
        msg = EmailMessage('Availability Submitted by ' + data[str(40)],
                           'Please find the Excel sheet attached',
                           from_email,
                           to_email)
        msg.content_subtype = "html"
        msg.attach_file(output_file)
        msg.send()
        return HttpResponse(JSONRenderer().render({"status": "Availability submitted"}), status=200)
    else:
        try:
            avail = Availability.objects.get(client_name=request.GET['client_name'], month=request.GET['month'])
        except ObjectDoesNotExist:
            return HttpResponse(json.dumps({"status": "Not found"}), 404)
        serializer = AvailabilitySerializer(avail)
        return HttpResponse(JSONRenderer().render(serializer.data), status=200)


@csrf_exempt
def update_sessions(request):
    if request.method == 'GET':
        # User has accepted a session
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
        # User has request to edit a session
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
        # User has cancelled a session
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
                message = request.GET['client_name'] + " has requested cancellation to the below session<br>" \
                          + "<br>Start Time - " + request.GET['start_time'] + "<br>End Time - " + request.GET[
                              'end_time'] + \
                          "<br>Date - " + request.GET['date']
            send_mail(request.GET['client_name'] + " has cancelled a session",
                      '',
                      from_email,
                      to_email,
                      html_message=message)
            return HttpResponse(json.dumps({'status': 'Cancelled'}), status=200)
        # User has raised query in the timesheet
        elif request.GET['action'] == 'RaiseQuery':
            try:
                session = Session.objects.get(client_name=request.GET['client_name'],
                                              start_time=request.GET['start_time'],
                                              end_time=request.GET['end_time'], date=request.GET['date'])
            except ObjectDoesNotExist:
                return HttpResponse(json.dumps({'status': 'Not Found'}), status=400)
            session.is_disputed = True
            session.disputed_message = request.GET['message']
            session.save()
            message = request.GET['client_name'] + " has raised concern for the below session in the Timesheet<br>" \
                      + "<br>Date - " + request.GET['date'] + "<br>Start Time - " + request.GET['start_time'] + \
                      "<br>End Time - " + request.GET['end_time'] + "<br>Query: " + request.GET['message']
            send_mail(request.GET['client_name'] + " has raised a concern in the Timesheet",
                      '',
                      from_email,
                      to_email,
                      html_message=message)
            return HttpResponse(json.dumps({'status': 'Concerned Raised'}), status=200)
        # User has accepted the timesheet
        elif request.GET['action'] == 'AcceptAll':
            Timesheet(client_name=request.GET['client_name'],
                      is_accepted=True,
                      month=int(request.GET['message']) + 1).save()
            send_mail(request.GET['client_name'] + " has accepted the Timesheet",
                      '',
                      from_email,
                      to_email)
            return HttpResponse(json.dumps({'status': 'Timesheet accepted'}), status=200)
        return HttpResponse(json.dumps({'status': 'Action not available'}), status=200)


@csrf_exempt
def parse_csv(request):
    if request.method == 'POST':
        if request.POST['button'] == 'Upload':
            csv_file = request.FILES['csv_file']
            result_list = check_csv(csv_file, request.POST['year'])
            return render(request, "home.html", {"result": result_list, "button_type": "Review", "file": csv_file})
        elif request.POST['button'] == 'Review':
            result_list = check_records(request.POST['data'])
            return render(request, "home.html", {"result": result_list, "button_type": "Submit"})
        elif request.POST['button'] == 'Submit':
            save_records(list(TempSession.objects.all()))
            return render(request, "home.html", {"button_type": "Saved"})
    return render(request, "home.html", {"button_type": "Upload"})


def check_csv(csv_file, year):
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
            date = datetime.strptime((row[2] + " " + str(year)).replace(" ", "/"), "%a/%b/%d/%Y").date()
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
    month = -1
    year = -1
    id = uuid.uuid1(4)
    for row in list(records):
        if name == "" or name != row.client_name:
            # records which are present in the admin panel but have been removed from csv
            for i in Session.objects.filter(client_name=name, date__month=row.date.month, date__year=row.date.year).exclude(updated_at=id):
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
            month = row.date.month
            year = row.date.year

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
    for i in Session.objects.filter(client_name=name, date__month=month,  date__year=year).exclude(updated_at=id):
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
