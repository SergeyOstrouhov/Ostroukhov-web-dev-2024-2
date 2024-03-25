from flask import Flask, render_template, session, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user
app = Flask(__name__)
application = app

# app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config.from_pyfile('config.py')

login_manager = LoginManager()
login_manager.init_app(application)

class User(UserMixin):
    def __init__(self, login, user_id):
        self.login = login
        self.id = user_id
    

@login_manager.user_loader
def load_user(user_id):
    users = user_list()
    for user in users:
        if user["id"] == user_id:
            return User(user["login"], user_id)
    return None

def user_list():
    return [{"id": "1", "login": "mario", "password": "1111"}]

@app.route('/')
def index():
    msg = 'Hello'
    return render_template('index.html', qq=msg)

@app.route('/login', methods=["POST", "GET"])
def login():
    
    if request.method == "POST":    
        name = request.form.get("login", False)
        password = request.form.get("password", False)
        db = user_list()
        text = "Ошибка логина"
        category = "alert-danger"
        for record in db:
            if record["login"] == name and record["password"] == password:
                user = User(record["login"], record["id"])
                login_user(user)
                return redirect(url_for("index"))
        
    return render_template('flask_login.html')



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))



@app.route('/counter')
def counter():
    if "counter" in session:
        session["counter"] += 1
    else:
        session["counter"] = 1 

    return render_template('counter.html')

# python3 -m venv ve
# . ve/bin/activate -- Linux
# ve\Scripts\activate -- Windows
# pip install flask python-dotenv