from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flaskr import backend
from google.cloud import storage



def make_endpoints(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'    

    class User(UserMixin):
        def __init__(self, user):
            self.name = user[0]
            self.username = user[1]
            self.id = user[2]

        def get_id(self):
            return self.id

        def is_authenticated(self):
            return True
        
        def is_active(self):
            return True

        def is_anonymous(self):
            return False

    @login_manager.user_loader
    def load_user(log=False, user_data=()):
        if log:
            user = User(user_data)
            return user
        else:
            return None

    # Flask uses the "app.route" decorator to call methods when users
    # go to a specific route on the project's website.
    # @app.route('name_of_page')
    
    @app.route("/")
    # @app.route('/main')
    def home():
        return render_template("main.html")

    # TODO(Project 1): Implement additional routes according to the project requirements.

    @app.route('/pages')
    def pages():
        return render_template('pages.html')

    @app.route('/pages/<sub_page>')
    def pages_next(sub_page):
        return render_template(f'{sub_page}.html')

    @app.route('/about')
    def about():
        return render_template('about.html')


    @app.route('/login', methods=['GET'])
    def get_login():
        return render_template('login.html')

    @app.route('/auth_login', methods=['POST'])
    def auth_login():

        user_check = {
            'username' : request.form.get('username'),
            'password' : request.form.get('password')
        }

        be = backend.Backend(app)
        valid_user = be.sign_in(user_check)
        
        if not valid_user[0]:
            return render_template('login.html', error='Incorret Username and/or Password')
            
        user = load_user(True, valid_user)
        login_user(user)

        return redirect(url_for('welcome'))
        
        

    @app.route('/welcome')
    @login_required
    def welcome():
        return render_template('welcome.html')

    @app.route('/upload')
    @login_required
    def upload():
        return render_template('upload.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return render_template('/')


    @app.route('/signup', methods=['GET'])
    def get_signup():
        return render_template('signup.html')

    @app.route('/auth_signup', methods=['POST'])
    def sign_up():

        new_user = {
            'name'     : request.form.get('Name'),
            'username' : request.form.get('Username'),
            'password' : request.form.get('Password')
        }

        if new_user['username'] == "" or new_user['password'] == "":
            return redirect("/")

        return redirect(url_for('welcome'))
