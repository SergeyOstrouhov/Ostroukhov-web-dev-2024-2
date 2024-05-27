from flask import Flask, render_template, redirect, url_for, request, make_response, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from my_sqldb import MyDb
import mysql.connector

app = Flask(__name__)

app.config.from_pyfile('config.py')

db = MyDb(app)

login_manager = LoginManager();

login_manager.init_app(app);

login_manager.login_view = 'login'
login_manager.login_message = 'Доступ к данной странице есть только у авторизованных пользователей '
login_manager.login_message_category = 'warning'

def get_roles():
    with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT * FROM roles')
            cursor.execute(query)
            roles = cursor.fetchall()
    return roles

class User(UserMixin):
    def __init__(self,user_id,user_login):
        self.id = user_id
        self.login = user_login
        

@login_manager.user_loader
def load_user(user_id):
    cursor= db.connect().cursor(named_tuple=True)
    query = ('SELECT * FROM users WHERE id=%s')
    cursor.execute(query,(user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
       return User(user.id,user.login)
    return None

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        login = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember')
        with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT * FROM users WHERE login=%s and password_hash=SHA2(%s,256) ')
            cursor.execute(query,(login, password))
            user_data = cursor.fetchone()
            if user_data:
                    login_user(User(user_data.id,user_data.login),remember=remember)
                    flash('Вы успешно прошли аутентификацию', 'success')
                    return redirect(url_for('list_users'))
        flash('Неверные логин или пароль', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('list_users'))

@app.route('/')
def list_users():
    with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id')
            cursor.execute(query)
            users = cursor.fetchall()
    return render_template('list_users.html', users = users)

def validate_login(text):
    for i in text:
        if not i.isdigit() and i not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
            return False, 'В login встречаются недопустимые символы.'
    if len(text) < 5:
        return False, 'Слишком короткий логин'
    return True, 'ок'


def validate_password(password):
    bad_length = False
    if not 8 <= len(password) <= 128:
        bad_length = True
    
    has_upper = False
    has_lower = False
    has_digit = False
    has_arabic_digit = False
    has_space = False
    bad_chrs = False
  
    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
            if char.isascii():
                has_arabic_digit = True
        elif char.isspace():
            has_space = True
    
    allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789~!?@#\$%^&*_+\(\)\[\]\{\}\>\<\./\\\|\"\'\. ,:"
  
    for char in password:
        if char not in allowed_chars:
            bad_chrs = True

    res = []
    if bad_length:
        res.append('Пароль должен быть больше 8 символов и меньше 128')
    if not has_upper:
        res.append('Пароль должен содежрать хотя бы одну заглавную букву\n')
    if not has_lower:
        res.append('Пароль долже содержать хотя бы одну строчную букву\n')
    if not has_digit:
        res.append('Пароль должен содержать хотя бы одну цифру\n')
    if not has_arabic_digit:
        res.append('Пароль должен содержать только арабские цифры\n')
    if has_space:
        res.append('Пароль не должен содержать пробелы\n')
    if bad_chrs:
        res.append('Пароль должен содежрать тольк одопустимые символы\n')

    if len(res) != 0:
        return False, res
    else:
        return True, res


@app.route('/create_user', methods=['GET','POST'])
@login_required
def create_user():
    roles = get_roles()
    if request.method == "POST":
        first_name = request.form.get('name')
        middle_name = request.form.get('middlename')
        last_name = request.form.get('lastname')
        login = request.form.get('login')
        password = request.form.get('password')
        role_id = request.form.get('role')
        val_log = validate_login(login)
        val_pas = validate_password(password)
        res_val = val_pas[1]
        if val_log[0]:
            if val_pas[0]:

                try:
                    with db.connect().cursor(named_tuple=True) as cursor:
                        query = ('INSERT INTO users (login, password_hash, first_name, middle_name, last_name, role_id) values(%s, SHA2(%s,256), %s, %s, %s, %s) ')
                        cursor.execute(query,(login, password, first_name, middle_name, last_name, role_id))
                        db.connect().commit()
                        flash('Вы успешно зарегестировали пользователя', 'success')
                        return redirect(url_for('list_users'))
                except mysql.connector.errors.DatabaseError:
                    db.connect().rollback()
                    flash('Ошибка при регистрации', 'danger')
            else:
                for i in res_val:
                    flash(i, 'danger')
                return render_template('create_user.html', roles = roles)
        else:
            flash(val_log[1], 'danger')
            return render_template('create_user.html', roles = roles)
            
    return render_template('create_user.html', roles = roles)

@app.route('/show_user/<int:user_id>')
@login_required
def show_user(user_id):
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
    return render_template('show_user.html', user = user )


@app.route('/edit_user/<int:user_id>', methods=['GET','POST'])
@login_required
def edit_user(user_id):
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

    if request.method == "POST":
        first_name = request.form.get('name')
        second_name = request.form.get('lastname')
        middle_name = request.form.get('middlename')
        role_id = request.form.get('role')
        try:
            with db.connect().cursor(named_tuple=True) as cursor:
                query = ('UPDATE users SET first_name=%s, middle_name=%s, last_name=%s, role_id = %s where id=%s;')
                cursor.execute(query,(first_name,  second_name, middle_name, role_id, user_id))
                db.connect().commit()
                flash('Вы успешно обновили пользователя', 'success')
                return redirect(url_for('list_users'))
        except mysql.connector.errors.DatabaseError:
            db.connect().rollback()
            flash('Ошибка при обновлении', 'danger')
    roles = get_roles()
    return render_template('edit_user.html', user = user, roles=roles)

@app.route('/delete_user/<int:user_id>', methods=["POST"])
@login_required
def delete_user(user_id): 
    with db.connect().cursor(named_tuple=True) as cursor:
        try:
            query = ('DELETE FROM users WHERE id=%s')
            cursor.execute(query, (user_id,))
            db.connect().commit()
            flash('Удаление успешно', 'success')
        except:
            db.connect().rollback()
            flash('Ошибка при удалении пользователя', 'danger')
    return redirect(url_for('list_users'))

@app.route('/new_pas/<int:user_id>', methods=["GET", "POST"])
@login_required
def change_password(user_id):
    if request.method == "POST":
        old_pass = request.form.get('password')
        new_password = request.form.get('password2')
        new_password2 = request.form.get('password3')
        with db.connect().cursor(named_tuple=True) as cursor:
            query = ('SELECT * FROM users WHERE id=%s and password_hash=SHA2(%s,256) ')
            cursor.execute(query,(user_id, old_pass))
            res = cursor.fetchone()
            if res:
                if validate_password(new_password):
                    if new_password == new_password2:
                        with db.connect().cursor(named_tuple=True) as cursor:
                            query = ('UPDATE users SET password_hash=SHA2(%s,256) WHERE id=%s')
                            cursor.execute(query,(new_password, user_id))
                            db.connect().commit()
                            flash('Вы успешно сменили пароль', 'success')
                            return redirect(url_for('list_users'))
                    else:
                        flash('Введённые пароли не совпадают', 'danger')
                        return render_template('change_password.html')
                else:
                    flash('Новый пароль не соответствует требованиям', 'danger')
                    return render_template('change_password.html')
            flash('Неверный пароль', 'danger')
            return render_template('change_password.html')
        
    return render_template('change_password.html')