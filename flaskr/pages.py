from flask import Flask, render_template, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flaskr import pages, backend
from google.cloud import storage



def make_endpoints(app):

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

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        
        user = {
            'username' : request.form.get('username'),
            'password' : request.form.get('password')
        }

        be = backend.Backend()
        valid_user = be.sign_in(user)
        if valid_user:
<<<<<<< HEAD
            #Display Name, Upload and Logout option now. (No longer able to access singup.html & login.html)
            return render_template('welcome.html')
=======
            #Display user Name, allow user to access Uploads page and Logout option. (No longer able to access singup.html & login.html)
            raise NotImplementedError
>>>>>>> 240e17181b384f9ff802faf4c1759b5ac3e51e2f
        
        return render_template('login.html', error='Incorret Username and/or Password')

    #Not sure if this is needed?
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

    @app.route('/signup', methods=['GET', 'POST'])
    def sign_up():
        new_user = {
            'username' : request.form.get('username'),
            'password' : request.form.get('password')
        }
        if new_user['username'] == "" or new_user['password'] == "":
            return
        return render_template('signup.html')
