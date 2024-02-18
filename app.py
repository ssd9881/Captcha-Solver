from flask import Flask, jsonify, request, render_template
from PIL import Image
import io
from captcha import CaptchaCracking
from werkzeug.utils import secure_filename
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

@app.route('/index', methods=['GET'])
def index():
    username=session.get('username', "Guest")
    return render_template('index.html', username=username)

@app.route('/index_guest', methods=['GET'])
def index_guest():
    username="Guest"
    return render_template('index copy.html', username=username)

# @app.route('/', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != 'admin' or request.form['password'] != 'admin':
#             error = 'Invalid Credentials. Please try again.'
#         else:
#             return redirect(url_for('index'))
#     return render_template('login.html', error=error)

app.secret_key = 'Captcha123'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Siddhant@08'
app.config['MYSQL_DB'] = 'captchalogin'
 
mysql = MySQL(app)
@app.route('/')
@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return render_template('index.html',username=username)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('landing'))
 


    
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

@app.route('/process_image', methods=['POST'])
def process_image():
    # name = request.args['name']
    # print("hi",name)
   
    username=session.get('username', 'Guest')
    # print(session['username'])
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    selected_option = request.form.get('type')

    file = request.files['file']

    try:
        img = Image.open(io.BytesIO(file.read()))
        
    except:
        return jsonify({'error': 'File is not an image'}), 400

    filename = secure_filename(file.filename)
    media_folder = os.path.join(app.static_folder, 'media')
    if not os.path.exists(media_folder):
        os.makedirs(media_folder)
    filepath = os.path.join(media_folder, filename)
    img.save(filepath)

    captcha_service = CaptchaCracking(filepath, selected_option)
    texts = captcha_service.captcha_cracking()

    result = {'result': texts, 'img': filename }
    
    
    return render_template('index.html', result=result, username=username)

if __name__ == '__main__':
    app.run(debug=True)
