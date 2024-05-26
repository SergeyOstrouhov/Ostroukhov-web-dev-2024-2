from functools import wraps
from check_rights import CheckRights
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask import Blueprint, render_template, redirect, send_file, url_for, request,flash
from app import db
from math import ceil
import io
bp = Blueprint('logs', __name__, url_prefix='/logs')

PER_PAGE = 5

@bp.route("/visits")
@login_required
def show_user_logs():
    logs=None
    page = int(request.args.get('page',1))
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT * FROM logs LIMIT %s OFFSET %s')
        cursor.execute(query, (PER_PAGE, (page-1) * PER_PAGE))
        logs=cursor.fetchall()
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT count(*) as count FROM logs')
        cursor.execute(query)
        count=cursor.fetchone().count
    return render_template("log/visits.html",logs=logs, count=ceil(count/PER_PAGE), page=page)

@bp.route("/users")
@login_required
def show_count_logs():
    logs=None
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT user_id,count(*) as count FROM logs group by user_id ')
        cursor.execute(query)
        logs=cursor.fetchall()
    return render_template("log/users.html",logs=logs)

@bp.route("/page")
@login_required
def show_page_logs():
    logs=None
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT path,count(*) as count FROM logs group by path ')
        cursor.execute(query)
        logs=cursor.fetchall()
    return render_template("log/page.html", logs=logs)

@bp.route("/export_csv")
@login_required
def export_csv():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT * FROM logs')
        cursor.execute(query)
        logs=cursor.fetchall()
    data = load_data(logs, ['user_id','path', 'created_at'])
    return send_file(data, as_attachment=True,download_name='download.csv')

def load_data(records, fields):
    csv_data=", ".join(fields)+"\n"
    for record in records:
        csv_data += ", ".join([str(getattr(record, field, '')) for field in fields]) + "\n"
    f = io.BytesIO()
    f.write(csv_data.encode('utf-8'))
    f.seek(0)
    return f