from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flaskr import backend
from google.cloud import storage
import os
import uuid
import zipfile
from flaskext.markdown import Markdown


def make_endpoints(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.session_protection = 'strong' 
    Markdown(app)       

    class User(UserMixin):
        def __init__(self, name):
            #TODO Doesnt display full name, but instead the id, fixit
            self.name = f'{name}'
            self.id = f'{uuid.uuid4()}'
        
        def get_id(self):
            return self.id

        def is_authenticated(self):
            return True
        
        def is_active(self):
            return True

        def is_anonymous(self):
            return False

    @login_manager.user_loader
    def load_user(name):
        user = User(name)
        return user
    
    @app.route('/')
    # @app.route('/main')
    def home():
        return render_template("main.html")

    @app.route('/pages')
    def pages():
        be = backend.Backend(app)
        page_names = be.get_all_page_names()
        return render_template('pages.html', page_names=page_names)

    @app.route('/pages/<sub_page>')
    def pages_next(sub_page):
        be = backend.Backend(app)
        be.get_wiki_page(sub_page)
        # html_content = be.get_wiki_page(sub_page)
        return render_template(f'{sub_page}.html')#, content=html_content)

    @app.route('/about')
    def about():
        be = backend.Backend(app)
        authors = be.get_about()
        return render_template('about.html', authors=authors)
    
    @app.route('/welcome')
    @login_required
    def welcome():
        return render_template('welcome.html')
        

    @app.route('/login', methods=['GET'])
    def get_login():
        return render_template('login.html')

    @app.route('/auth_login', methods=['POST'])
    def auth_login():

        user_check = {
            'username' : request.form.get('Username'),
            'password' : request.form.get('Password')
        }

        be = backend.Backend(app)
        valid, data = be.sign_in(user_check)
        
        if not valid:
            return render_template('login.html', error='Incorret Username and/or Password')
        
        print(data)
        user = load_user(data)
        login_user(user)

        return redirect(url_for('welcome'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect('/')

    @app.route('/upload', methods=['GET','POST'])
    @login_required
    def upload(): 
        #TODO doesn't properly route to the user's system 
        #TODO A user can overwrite a pre-existing file, some check should to be created when uploading
        #TODO A user should be able to upload .md files
        if request.method == 'POST':
            uploaded_file = request.files['upload']
            filename = os.path.basename(uploaded_file.filename)
            print("FILENAME",filename)
            #case where the file is an image
            if filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png') or filename.endswith('.md'):
                uploadImage(uploaded_file, filename)
                return redirect(url_for("home"))
            #case where the file is a zip
            elif filename.endswith('.zip'):
                with zipfile.ZipFile(uploaded_file, 'r') as z:
                    for zipped_image in z.namelist():
                        #upload the files that are images only
                        if zipped_image.endswith('.jpg') or zipped_image.endswith('.jpeg') or zipped_image.endswith('.png'):
                            uploadImage(z.open(zipped_image), zipped_image)
                            print("FILENAME",zipped_image)
                return redirect(url_for("home"))
            else:
                render_template('upload.html', error='Incorrect File Type')

        return render_template('upload.html')

    def uploadImage(f, filename):
        be = backend.Backend(app)
        return be.upload(f, filename)

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

        be = backend.Backend(app)
        valid, data = be.sign_up(new_user)

        if not valid:
            return render_template('signup.html', error='User already exists')
        
        user = load_user(data)
        login_user(user)

        return redirect(url_for('welcome'))
        
    @app.route('/images', methods=['GET', 'POST'])
    def get_allimages():
        be = backend.Backend(app)
        image_lst = be.get_image()
        return render_template('images.html', image_lst=image_lst)
        
    @app.errorhandler(405)
    def invalid_method(error):
        flash('Incorrect method used, try again')
        return redirect(url_for('/')), 405

    """
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <ul class=flashes>
            {% for message in messages %}
                <li>{{ message }}</li>
            {% endfor %}
            </ul>
        {% endif %}
    {% endwith %}
    """