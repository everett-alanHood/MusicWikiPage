
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from google.cloud import storage
import os
import uuid
import zipfile
from flaskext.markdown import Markdown
import csv

def make_endpoints(app, Backend):
    """Connects the frontend with the established routes and the backend.

    Attributes:
        app: Flask instance.
        login_manager: LoginManager object that takes care of the user's login.
        Markdown: Converts the contents of Markdown files to readable text.
    """

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
    Markdown(app)
    Back_end = Backend(app)



    class User(UserMixin):
        """User Class that is used by the Login Manager and browser.

        It is stored in user's browser and is used to authorize the user when using the wiki.

        Attributes:
            name: String representation of User's name
            id: UUID identifier for the user
            
        """

        def __init__(self, name):
            """Initializes the User object with the name passed as parameter and assigns it an UUID.

            Args:
                name: String representation of the user's name
            """
            self.name = f'{name}'
            self.id = f'{uuid.uuid4()}'

        def get_id(self):
            return self.name

        def is_authenticated(self):
            return True

        def is_active(self):
            return True

        def is_anonymous(self):
            return False

    @login_manager.user_loader
    def load_user(name):
        """
        Creates and returns a User object with name passed as parameter.

        Args:
            name: String representation of user's name.
        """
        user = User(name)
        return user

    @app.route('/')
    # @app.route('/main')
    def home():
        """Returns the Home page.

        GET: Home page
        """
        if Back_end.current_username != "":
            Back_end.add_to_history("Home")
        return render_template("main.html")

    @app.route('/pages', methods=['GET','POST'])
    def pages():
        """Description: Have two hyperlink that give the sorting method that the hyperlink for 
                  subpages will display \n
        Args:
            - None
        Return:
            - returns flask function consisting of pages.html, string and list of 
              page names"""
        page_names = Back_end.get_all_page_names()
        sort="Alphabetical"

        if request.args.get("sort_by")=="Popularity":
            sort="Popularity"
            page_names=Back_end.page_sort_by_popularity()
            #get list of page names by Popularity
        # default list is equal to Alphabetically
        return render_template('pages.html', sort=sort, page_names=page_names)
        

    @app.route('/pages/<sub_page>')
    def pages_next(sub_page):
        """Returns the parametrized sub_page page. It uses the sub_page passed as part of the route to 
        check the Backend for the corresponding wiki page and sends the user to that user-selected markdown file that is now displayed as HTML.

        GET: Gets the corresponding MD file from the Backend, sends the user to a new page that displays the MD as HTML.
        """
        if Back_end.current_username != "":
            sub_page_cap=sub_page.capitalize()
            Back_end.add_to_history(sub_page_cap)
            
        html_content = Back_end.get_wiki_page(sub_page)    
        return render_template(f'sub_pages.html', content=html_content)

    #@app.route('/pages', methods=['GET'])
    #def dropdown():
        #sort_by=["Alphabetically","Popularlity"]
        #return render_template("pages.html",sort_by=sort_by)

    @app.route('/about')
    def about():
        """Calls the backend and fetches all authors name and picture, then it sends the users to the about page and display all of the wiki author's name and picture.

        GET: Calls Backend to get all Authors information and pictures, then sends the user to the about page that shows all the author's corresponding info.
        """
        if Back_end.current_username != "":
            Back_end.add_to_history("About")
        authors = Back_end.get_about()
        return render_template('about.html', authors=authors)

    @app.route('/welcome')
    @login_required
    def welcome():
        """Returns the Welcome page.

        GET: Welcome page
        """
        return render_template('welcome.html')

    @app.route('/login', methods=['GET'])
    def get_login():
        """Returns the login page.

        GET: Login page
        """
        return render_template('login.html')

    @app.route('/auth_login', methods=['POST'])
    def auth_login():
        """It takes the username, password passed as input fields in the login page and calls the Backend to check for validity.
        If valid it logs in the user and redirects the user to the welcome page. Else, The user is taken back to the login page and it returns an error.

        POST: Takes login info from input fields in login and tries to log in user,
        if successful redirects the user to the welcome page, else it returns the user to the login page with an error message.
        """

        user_check = {
            'username': request.form.get('Username'),
            'password': request.form.get('Password')
        }

        # be = backend.Backend(app)
        valid, data = Back_end.sign_in(user_check)

        if not valid:
            return render_template('login.html',
                                   error='Incorrect Username and/or Password')

        user = load_user(data)
        login_user(user)
        return redirect(url_for('welcome'))

    @app.route('/logout')
    @login_required
    def logout():
        """Logs out user and takes them to the initial page.

        GET: Log out and redirects user to initial page
        """
        if Back_end.current_username != "":
            Back_end.add_to_history("Logged Out")
        logout_user()
        return redirect('/')

    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        """When there is a POST response it takes the uploaded file/s, processes it, checks for validity and sents it to the Backend,
        where it will be store in the appropiate GCS bucket depending on the type of content it is. (images or markdowns)

        GET: Upload Page
        POST: Takes the file passed as an input in the form and sents it to the Backend, redirects the user to the Home page.
        """

        #TODO A user can overwrite a pre-existing file, some check should to be created when uploading
        if Back_end.current_username != "":
            Back_end.add_to_history("Upload")
        if request.method == 'POST':
            uploaded_file = request.files['upload']
            filename = os.path.basename(uploaded_file.filename)
            print("FILENAME", filename)
            file_end = filename.split(".")[-1].lower()
            #case where the file is an image
            #if filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png') or filename.endswith('.md'):
            if file_end == "jpeg" or file_end == "jpg" or file_end == "png" or file_end == "md":
                Back_end.upload(uploaded_file, filename)
                return redirect(url_for("home"))
            #case where the file is a zip
            elif filename.endswith('.zip'):
                with zipfile.ZipFile(uploaded_file, 'r') as z:
                    for zipped_image in z.namelist():
                        zip_end = zipped_image.split(".")[-1].lower()
                        #upload the files that are images only
                        if zipped_image.endswith(
                                '.jpg') or zipped_image.endswith(
                                    '.jpeg') or zipped_image.endswith('.png'):
                            Back_end.upload(z.open(zipped_image), zipped_image)
                            print("FILENAME\nrfeionffoij", zipped_image)
                return redirect(url_for("home"))
            else:
                return render_template('upload.html',
                                       error='Incorrect File Type')
        return render_template('upload.html')

    @app.route('/comments', methods=['GET', 'POST'])
    @login_required
    def comments_page():
        """Displays all fetched Google Cloud Bucket blobs from the comments bucket as comments with the username, time of posting and content being displayed. 
        When a POST request is received it takes the information passed in the
        form and creates a blob containing it that is uploaded to the Google Cloud Storage comments bucket. 

        GET: Comments page with input form for users to upload their own content.
        POST: Takes the message passed as an input in the form and sents it to the Backend, refreshes the page to display newly created comments.
        """
        Back_end.add_to_history("Comments")
        comment_list = Back_end.get_comments()
        if request.method == 'POST':
            message = request.form.get("comment")
            author = request.form.get("hidden")
            if not message:
                return render_template('comments.html',
                                       comment_list=comment_list , error='Comment content is empty. Invalid Comment. Please fill out the form.')
            if len(message) > 500:
                return render_template('comments.html',
                                       comment_list=comment_list , error='Comment is too long, limit your message to 500 characters.')
            uploaded = Back_end.upload_comment(author, message)
            if uploaded:
                print("File was uploaded Succesfully")
            comment_list = Back_end.get_comments()
        return render_template('comments.html', comment_list=comment_list)

    @app.route('/signup', methods=['GET'])
    def get_signup():
        """Returns the signup page.

        GET: Sign Up page
        """
        return render_template('signup.html')

    @app.route('/auth_signup', methods=['POST'])
    def sign_up(load_user=load_user):
        """When response is POST it takes the name, username, password information in the form and passes it on to the Backend to confirm if valid.
        If valid, it logins the user and redirects it to the Welcome page, else: it returns an error and the same page.

        POST: Passes form to Backend and confirms login, redirects to Welcome page.
        """
        new_user = {
            'name': request.form.get('Name'),
            'username': request.form.get('Username'),
            'password': request.form.get('Password')
        }

        valid, data = Back_end.sign_up(new_user)

        if not valid:
            return render_template('signup.html', error='User already exists')

        user = load_user(data)
        login_user(user)
        return redirect(url_for('welcome'))

    @app.route('/images', methods=['GET', 'POST'])
    def get_allimages():
        """It uses the Backend to look for all images in the GCS image bucket and returns a list of links to each one.
        It sends the user to the Images page and passes the image list as a parameter.

        GET: Calls Backend and fetch images, sends user to the Images page where are images are displayed.
        """
        if Back_end.current_username != "":
            Back_end.add_to_history("Images")
        image_lst = Back_end.get_image()
        return render_template('images.html', image_lst=image_lst)

    @app.errorhandler(405)
    def invalid_method(error):
        """Error handler that manages all the pages error and forwards the user to the initial page.

        Args:
            error: Error number representing the type of error the user got.
        """
        flash('Incorrect method used, try again')
        return redirect(url_for('home')), 405

    @app.route('/log')
    def log():
        return render_template('log.html')

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

    @app.route('/history', methods=['GET', 'POST'])
    def history():
        '''This takes the user's history and sendss it to the frontend page history.html to display the user's history.
        Personal preference, but the code below isn't necessary since the user doesn't need to know they're viewing their history.'''
        # if Back_end.current_username is not "":
        #     Back_end.add_to_history("History")
        history_summary = Back_end.get_history()
        history_summary.reverse()
        user_name = Back_end.current_username        
        return render_template('history.html', history_summary = history_summary, user_name = user_name)