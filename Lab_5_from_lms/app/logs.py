from functools import wraps
from check_rights import CheckRights
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask import Blueprint, render_template, redirect, send_file, url_for, request,flash
from app import db
from math import ceil
import io
bp = Blueprint('logs', __name__, url_prefix='/logs')
from auth import checkRole
PER_PAGE = 5

# @bp.route("/visits")
# @login_required
# def show_user_logs():
#     logs=None
#     page = int(request.args.get('page',1))
#     #if current_user.is_admin == 1:
#     with db.connect().cursor(named_tuple=True) as cursor:
#         query = ('SELECT * FROM logs LIMIT %s OFFSET %s')
#         cursor.execute(query, (PER_PAGE, (page-1) * PER_PAGE))
#         logs=cursor.fetchall()
#     with db.connect().cursor(named_tuple=True) as cursor:
#         query = ('SELECT count(*) as count FROM logs')
#         cursor.execute(query)
#         count=cursor.fetchone().count
#     #else:
#         # with db.connect().cursor(named_tuple=True) as cursor:
#             # query = ('SELECT * FROM logs WHERE user_id = %s LIMIT %s OFFSET %s')
#             # cursor.execute(query, (current_user(), PER_PAGE, (page-1) * PER_PAGE))
#             # logs=cursor.fetchall()
#         # with db.connect().cursor(named_tuple=True) as cursor:
#             # query = ('SELECT count(*) WHERE user_id = %s as count FROM logs')
#             # cursor.execute(query, (current_user()))
#             # count=cursor.fetchone().count
#     return render_template("log/visits.html",logs=logs, count=ceil(count/PER_PAGE), page=page)

@bp.route("/visits")
@login_required
def show_user_logs():
    logs=None
    page = int(request.args.get('page',1))

    with db.connect().cursor(named_tuple=True) as cursor:
        if (current_user.can('prev_logs', current_user) == True):
            query = 'SELECT logs.*, users.first_name, users.last_name, users.middle_name FROM logs LEFT JOIN users ON logs.user_id = users.id ORDER BY id DESC LIMIT %s OFFSET %s '
            cursor.execute(query, (PER_PAGE, (page - 1) * PER_PAGE))
        else:
            query = f'SELECT * FROM logs WHERE user_id = {int(current_user.id)} LIMIT %s OFFSET %s'
            cursor.execute(query, (PER_PAGE, (page - 1) * PER_PAGE))
        logs = cursor.fetchall()

    processed_logs = []
    for log in logs:
        if log.user_id == "Неаутентифицированный пользователь":
            processed_logs.append(log)
        else:
            fio = f"{log.middle_name} {log.first_name} {log.last_name}"
            processed_logs.append(log._replace(user_id=fio))

    print(logs)

    with db.connect().cursor(named_tuple=True) as cursor:
        if (current_user.can('prev_logs', current_user) == True):
            query = 'SELECT count(*) as count FROM logs'
            cursor.execute(query)
        else:
            query = f'SELECT count(*) as count FROM logs WHERE user_id = {int(current_user.id)}'
            cursor.execute(query)
        count = cursor.fetchone().count

    return render_template("log/visits.html", logs=processed_logs, count=ceil(count/PER_PAGE), page=page)

@bp.route("/users")
@login_required
@checkRole("prev_logs")
def show_count_logs():
    logs=None
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT user_id, users.first_name, users.last_name, users.middle_name, count(*) as count FROM logs LEFT JOIN users ON logs.user_id = users.id  group by user_id ORDER BY count DESC')
        cursor.execute(query)
        logs=cursor.fetchall()
    processed_logs = []
    for log in logs:
        if log.user_id == "Неаутентифицированный пользователь":
            processed_logs.append(log)
        else:
            fio = f"{log.middle_name} {log.first_name} {log.last_name}"
            processed_logs.append(log._replace(user_id=fio))
    return render_template("log/users.html",logs=processed_logs)

@bp.route("/page")
@login_required
@checkRole("prev_logs")
def show_page_logs():
    logs=None
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT path,count(*) as count FROM logs group by path order by count DESC')
        cursor.execute(query)
        logs=cursor.fetchall()
    return render_template("log/page.html", logs=logs)

@bp.route("/export_csv")
@login_required
def export_csv():
    if (current_user.can('prev_logs', current_user) == True):
        with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT logs.*, users.first_name, users.last_name, users.middle_name FROM logs LEFT JOIN users ON logs.user_id = users.id ORDER BY id DESC')
            cursor.execute(query)
            logs=cursor.fetchall()
        
    else:
        with db.connect().cursor(named_tuple=True) as cursor:
            query = (f'SELECT * FROM logs WHERE user_id = {int(current_user.id)}')
            cursor.execute(query)
            logs=cursor.fetchall()
        
    processed_logs = []
    for log in logs:
        if log.user_id == "Неаутентифицированный пользователь":
            processed_logs.append(log)
        else:
            fio = f"{log.middle_name} {log.first_name} {log.last_name}"
            processed_logs.append(log._replace(user_id=fio))
    data = load_data(processed_logs, ['user_id','path', 'created_at'])
    return send_file(data, as_attachment=True,download_name='download.csv')

@bp.route("/export_csv_pages")
@login_required
def export_csv_pages():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT path,count(*) as count FROM logs group by path order by count')
        cursor.execute(query)
        logs=cursor.fetchall()
    
    data = load_data(logs, ['path', 'count'])
    return send_file(data, as_attachment=True,download_name='download_pages.csv')

@bp.route("/export_csv_users")
def export_csv_users():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT user_id, users.first_name, users.last_name, users.middle_name, count(*) as count FROM logs LEFT JOIN users ON logs.user_id = users.id  group by user_id ORDER BY count DESC')
        cursor.execute(query)
        logs=cursor.fetchall()
    processed_logs = []
    for log in logs:
        if log.user_id == "Неаутентифицированный пользователь":
            processed_logs.append(log)
        else:
            fio = f"{log.middle_name} {log.first_name} {log.last_name}"
            processed_logs.append(log._replace(user_id=fio))
    data = load_data(processed_logs, ['user_id', 'count'])
    # print(data)
    return send_file(data, as_attachment=True,download_name='download_users.csv')

def load_data(records, fields):
    csv_data=", ".join(fields)+"\n"
    for record in records:
        csv_data += ", ".join([str(getattr(record, field, '')) for field in fields]) + "\n"
    f = io.BytesIO()
    f.write(csv_data.encode('utf-8'))
    f.seek(0)
    return f