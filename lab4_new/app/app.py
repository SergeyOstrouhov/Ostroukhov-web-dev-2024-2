from flask import Flask, render_template, redirect, url_for, request, make_response, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from my_sqldb import MyDb
import mysql.connector
import re

app = Flask(__name__)

app.config.from_pyfile('config.py')

db = MyDb(app)

login_manager = LoginManager();

login_manager.init_app(app);

login_manager.login_view = 'login'
login_manager.login_message = 'Доступ к данной странице есть только у авторизованных пользователей '
login_manager.login_message_category = 'warning'

def get_roles():
    cursor = db.connect().cursor(named_tuple=True)
    query = ('SELECT * FROM roles')
    cursor.execute(query)
    roles = cursor.fetchall()
    return roles

class User(UserMixin):
    def __init__(self, user_id, user_login):
        self.id = user_id
        self.login = user_login
        

@login_manager.user_loader
def load_user(user_id):
    cursor = db.connect().cursor(named_tuple=True)
    query = ('SELECT * FROM users WHERE id=%s')
    cursor.execute(query,(user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
       return User(user.id,user.login)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "POST":
        login = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember')
        cursor = db.connect().cursor(named_tuple=True)
        query = ('SELECT * FROM users WHERE login=%s and password_hash=SHA2(%s,256) ')
        cursor.execute(query, (login, password))
        user_data = cursor.fetchone()
        if user_data:
            login_user(User(user_data.id,user_data.login),remember=remember)
            flash('Вы успешно прошли аутентификацию', 'success')
            return redirect(url_for('index'))
        flash('Неверные логин или пароль', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/list_users')
@login_required
def list_users():
    cursor = db.connect().cursor(named_tuple=True)
    query = ('SELECT * FROM users')
    cursor.execute(query)
    users = cursor.fetchall()
    return render_template('list_users.html', users = users)

@app.route('/create_user', methods=['GET','POST'])
@login_required
def create_user():
    user_create_data = {
        'name': '',
        'lastname': '',
        'middlename': '',
        'login': '',
        'password': '',
        'role_id': ''
    }

    current_errors = {}

    if request.method == "POST":
        first_name = request.form.get('name')
        second_name = request.form.get('lastname')
        middle_name = request.form.get('middlename')
        login = request.form.get('login')
        password = request.form.get('password')
        role_id = request.form.get('role')

        user_create_data = {
            'first_name': request.form.get('name'),
            'second_name': request.form.get('lastname'),
            'middle_name': request.form.get('middlename'),
            'login': request.form.get('login'),
            'password': request.form.get('password'),
            'role_id': request.form.get('role')
        }

        error_first = False
        error_password = False
        error_second = False
        error_login = False
        error_password_1 = False
        error_password_2 = False
        error_password_3 = False
        error_password_4 = False
        error_password_5 = False

        if not (first_name):
            error_first = 'Поле не может быть пустым'

        if not (password):
            error_password = 'Поле не может быть пустым'

        if not (second_name):
            error_second = 'Поле не может быть пустым'

        if not (login):
            error_login = 'Поле не может быть пустым'

        if len(login) < 5 : 
            error_login = 'Логин должен иметь длину не менее 5 символов'
        
        for i in login:
            if i not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
                error_login += "\n Логин должен состоять только из латинских букв и цифр "

        if not (8 <= len(password) <= 128):
            error_password_1 = 'Пароль должен содержать от 8 до 128 символов'

        for i in password:
            if i not in  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789~!?@#\$%^&*_+\(\)\[\]\{\}\>\<\./\\\|\"\'\. ,:":
                error_password_2 = 'Пароль должен состоять только из латинских и кирилических букв, цифр и символов: ~ ! ? @ # $ % ^ & * ( ) { } [ ] < > / \ | " \' . , : ; + - _'
        
                
        if not re.search(r'[a-z]', password):
            error_password_3 = 'Пароль должен содержать как минимум одну строчную букву'

        if not re.search(r'[A-Z]', password):
            error_password_4 = 'Пароль должен содержать как минимум одну заглавную букву'

        if not re.search(r'\d', password):
            error_password_5 = 'Пароль должен содержать как минимум одну цифру'

        errors = {
            'error_first': error_first,
            'error_password': error_password,
            'error_second': error_second,
            'error_login': error_login,
            'error_password_1': error_password_1,
            'error_password_2': error_password_2,
            'error_password_3': error_password_3,
            'error_password_4': error_password_4,
            'error_password_5': error_password_5
        }

        # Фильтруем ошибки, которые не равны False
        # current_errors = {name: error for name, error in errors.items() if error != False}
        current_errors = {}
        for key, value in errors.items():
            if value:
                current_errors[key] = value 
        # Если есть хотя бы одна ошибка
        if current_errors:
            # print(current_errors)
            return render_template('create_user.html', user_create_data=user_create_data, roles=get_roles(), current_errors=current_errors)



        try:
            cursor = db.connect().cursor(named_tuple=True)
            query = ('INSERT INTO users (login, password_hash, first_name, last_name, middle_name, role_id) values(%s, SHA2(%s,256), %s, %s, %s, %s) ')
            cursor.execute(query,(login, password, first_name, second_name, middle_name, role_id))
            db.connect().commit()
            flash('Вы успешно зарегестировали пользователя', 'success')
            return redirect(url_for('list_users'))
        except mysql.connector.errors.DatabaseError:
            db.connect().rollback()
            flash('Ошибка при регистрации', 'danger')

    roles = get_roles()
    return render_template('create_user.html',user_create_data = user_create_data, roles = roles, current_errors=current_errors)

@app.route('/show_user/<int:user_id>')
@login_required
def show_user(user_id):
    cursor = db.connect().cursor(named_tuple=True)
    query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    print(user)
    return render_template('show_user.html', user = user )


@app.route('/edit_user/<int:user_id>', methods=['GET','POST'])
@login_required
def edit_user(user_id):
    current_errors = {}

    cursor = db.connect().cursor(named_tuple=True)
    query = ('SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s')
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()

    if request.method == "POST":
        first_name = request.form.get('name')
        second_name = request.form.get('lastname')
        middle_name = request.form.get('middlename')

        try:
            cursor = db.connect().cursor(named_tuple=True)
            query = ('UPDATE users SET first_name=%s, second_name=%s, middle_name=%s where id=%s;')
            cursor.execute(query,(first_name,  second_name, middle_name, user_id))
            db.connect().commit()
            flash('Вы успешно обновили пользователя', 'success')
            return redirect(url_for('list_users'))
        except mysql.connector.errors.DatabaseError:
            db.connect().rollback()
            flash('Ошибка при обновлении', 'danger')
    return render_template('edit_user.html', user = user, current_errors=current_errors)

@app.route('/delete_users/<int:user_id>', methods=['GET','POST'])
@login_required
def delete_user(user_id):
    if request.method == "POST":
        try:
            cursor = db.connect().cursor(named_tuple=True)
            query = ('DELETE FROM users WHERE id=%s')
            cursor.execute(query, (user_id,))
            db.connect().commit()
            flash('Удаление успешно', 'success')
        except:
            db.connect().rollback()
            flash('Ошибка при удалении пользователя', 'danger')
    return redirect(url_for('list_users'))

@app.route('/changing_password/', methods=['GET','POST'])
@login_required
def changing_password():
    current_errors = {}
    change_data = {
        "Old_pass": "",
        "new_pass": "",
        "new_pass_2": ""
    }
    if request.method == "POST":
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        password = request.form.get('password')
        change_data['Old_pass'] = old_password
        change_data['new_pass'] = new_password
        change_data['new_pass_2'] = password

        error_old_password_none = False
        error_new_password_none = False
        error_password_none = False
        error_password = False
        error_password_1 = False
        error_password_2 = False
        error_password_3 = False
        error_password_4 = False
        error_password_5 = False

        if not (old_password):
            error_old_password_none = 'Поле старый пароль не может быть пустым'

        if not (new_password):
            error_new_password_none = 'Поле новый пароль не может быть пустым'

        if not (password):
            error_password_none = 'Поле повтор пароля не может быть пустым'

        if not (new_password == password):
            error_password = 'Новые пароли должны совпадать'

        if not (8 <= len(new_password) <= 128):
            error_password_1 = 'Пароль должен содержать от 8 до 128 символов'

        if not re.match(r'^[a-zA-Zа-яА-Я0-9~!?@#$%^&*(){}\[\]<>\\/|"\'.,:;+-_]*$', new_password):
            error_password_2 = 'Пароль должен состоять только из латинских и кирилических букв, цифр и символов: ~ ! ? @ # $ % ^ & * ( ) { } [ ] < > / \ | " \' . , : ; + - _'

        if not re.search(r'[a-z]', new_password):
            error_password_3 = 'Пароль должен содержать как минимум одну строчную букву'

        if not re.search(r'[A-Z]', new_password):
            error_password_4 = 'Пароль должен содержать как минимум одну заглавную букву'

        if not re.search(r'\d', new_password):
            error_password_5 = 'Пароль должен содержать как минимум одну цифру'


        errors = {
            'error_old_password_none': error_old_password_none,
            'error_new_password_none':  error_new_password_none,
            'error_password_none':  error_password_none,
            'error_password': error_password,
            'error_password_1': error_password_1,
            'error_password_2': error_password_2,
            'error_password_3': error_password_3,
            'error_password_4': error_password_4,
            'error_password_5': error_password_5
        }

        # Фильтруем ошибки, которые не равны False
        current_errors = {name: error for name, error in errors.items() if error != False}

        # Если есть хотя бы одна ошибка
        if current_errors:
            print(current_errors)
            return render_template('changing_password.html', roles=get_roles(), change_data=change_data, current_errors=current_errors)

        try:
            cursor = db.connect().cursor(named_tuple=True)
            query = ('UPDATE users SET password_hash=SHA2(%s,256) where id=%s;')
            cursor.execute(query, (password, current_user.id))
            db.connect().commit()
            flash('Вы успешно сменили пароль', 'success')
            return redirect(url_for('changing_password'))
        except mysql.connector.errors.DatabaseError:
            db.connect().rollback()
            flash('Ошибка при смене пароля', 'danger')

    return render_template('changing_password.html', change_data=change_data, current_errors=current_errors)

if __name__ == "__main__":
    app.run(debug=True)