from flask import Flask, render_template, request, make_response

def validate_phone_number(phone_number):
    for ch in phone_number:
        if not ch.isdigit() and ch not in '+-.() ':
            return False, 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
    l = 0
    for i in phone_number:
        if i.isdigit():
            l += 1
    
    if l > 11 or l < 10:
        return False, 'Недопустимый ввод. Неверное количество цифр.'
    return True, 'ok'
    # Проверка символов
    

def format_phone_number(phone_number):
    phone_number = ''.join(ch for ch in phone_number if ch.isdigit())
    formatted_number = phone_number
    l = len(phone_number)
    if l == 11:
        phone_number = phone_number[1:11]
    
    formatted_number = '8-{}-{}-{}-{}'.format(phone_number[0:3], phone_number[3:6], phone_number[6:8], phone_number[8:])

    return formatted_number


app = Flask(__name__)
application = app

@app.route('/')
def index():
    url = request.url
    return render_template('index.html', url = url)
@app.route('/args')
def args():
    return render_template('args.html')

@app.route('/headers')
def headers():
    return render_template('headers.html')

@app.route('/cookies')
def cookies():
    response = make_response(render_template('cookies.html'))
    if "user"  not in request.cookies:
        response.set_cookie("user","куки")
    else:
        response.delete_cookie("user")
    return response

@app.route('/phone', methods = ['GET', 'POST'])
def phone():
    res = ""
    tel = request.form.get("number")
    if request.method == "POST":
        if request.form.get("number","") != "":
            res, otv = validate_phone_number(tel)
            res = "is-valid" if res else "is-invalid"
            if res == 'is-valid':
                return render_template("phone.html", category = res, otv = format_phone_number(tel))
            return render_template("phone.html", category = res, otv = otv)
    else:
        return render_template("phone.html", category = res)