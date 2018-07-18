from flask import Flask, render_template, flash, request, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
# config MySql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ilove7089'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# initialize mysql
mysql = MySQL(app)

# app.debug = true
@app.route('/')
def index():
   return render_template('home.html')

@app.route('/about')
def about(): 
    return render_template('about.html')

@app.route('/articles')
def articles():
    #create cursor
    cur = mysql.connection.cursor()
    #Get articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0 :
        return render_template('articles.html', articles=articles)
    else: 
        msg = 'No Articles found'
        return render_template('articles.html', msg = msg)
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    #create cursor
    cur = mysql.connection.cursor()
    #Get articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    return render_template('article.html', article=article)

class RegisterForm(Form):
    name = StringField('Name', [validators.length(min=1, max=50)])
    username = StringField('Username', [validators.length(min=4, max=25)])
    email = StringField('Email', [validators.length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('conirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate: 
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # commit to db
        mysql.connection.commit()
        # close connection
        cur.close()
        flash('success, -> login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #Get form fields
        email = request.form['email']
        password_candidate = request.form['password']
        #create cursor
        cur = mysql.connection.cursor()
        #GET USER BY EMAIL
        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])
        if result > 0:
            #GET the stored hash 
            data = cur.fetchone()
            password = data['password']
            username = data['username']
            #compare password
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else: 
                error = 'invalid login'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Email not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

#check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else: 
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/dashboard')
@is_logged_in
def dashboard(): 
    #create cursor
    cur = mysql.connection.cursor()
    #Get articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0 :
        return render_template('dashboard.html', articles=articles)
    else: 
        msg = 'No Articles found'
        return render_template('dashboard.html', msg = msg)
    cur.close()

class ArticleForm(Form):
    title = StringField('Title', [validators.length(min=1, max=200)])
    body = TextAreaField('Body', [validators.length(min=10)])

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create cursor
        cur = mysql.connection.cursor()
        #execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
        #commit to DB
        mysql.connection.commit()
        #close connection
        cur.close()

        flash('Article created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form = form)

#edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    #create cursor 
    cur = mysql.connection.cursor()
    #get article by id
    result = cur.execute("SELECT * from articles WHERE id = %s", [id])
    article = cur.fetchone()
    #GET form
    form = ArticleForm(request.form)
    #populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create cursor
        cur = mysql.connection.cursor()
        #execute
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        #commit to DB
        mysql.connection.commit()
        #close connection
        cur.close()

        flash('Article updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form = form)

#delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    #cursor
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Article deleted', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'secret1234'
    app.run(debug=True)
# 1. Clean up the app.py into separate modules
# 2. Customize it with your own stylesheets and javascript
# 3. Add another layer of access control to delete_article (The users can create a fake html form to send post requests to /delete_article and delete other peoples articles.)
# 4. Prevent users from registering the same username as other users.