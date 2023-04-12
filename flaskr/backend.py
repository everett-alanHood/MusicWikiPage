from google.cloud import storage
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from datetime import datetime
#Hasing password
import bcrypt  #gensalt, hashpw, checkpw
import base64
import hashlib
import os
# from markdown import markdown
import markdown
import re
from collections import deque
"""
Args:
Explain:
Returns:
Raises:
"""


class Backend:
    """
    Explain

    
    Attributes:
        bucket_content: 
        bucket_users: 
        bucket_images: 
        pages: Set of all pages on necessary pages on wiki
        sub_pages: Set of all sub-pages to pages.html
        all_pages: All valid pages on the wiki (Union of pages and sub_pages)
    """

    def __init__(self, app, SC=storage.Client()):
        """
        Args: 
            An App from flask (ex. Flask(__name__) )
        Explain: 
            Initializes and creates necessary attributes for backend
        """
        test_app = Flask(__name__)
        self.login_manager = LoginManager()
        self.login_manager.init_app(test_app)
        #Buckets
        storage_client = SC
        self.bucket_content = storage_client.bucket('minorbugs_content')
        self.bucket_users = storage_client.bucket('minorbugs_users')
        self.bucket_images = storage_client.bucket('minorbugs_images')
        self.bucket_users.bucket_history = storage_client.bucket('user_history')        
        #page urls
        self.pages = {
            '/', 'pages', 'about', 'welcome', 'login', 'logout', 'upload',
            'signup', 'images', 'history'
        }
        self.sub_pages = {
            'chord', 'harmony', 'pitch', 'rhythm', 'melody', 'scales', 'timbre',
            'form', 'dynamics', 'texture'
        }
        self.all_pages = self.pages | self.sub_pages
        self.current_username = ""

    def get_history(self):
        user_blob = self.bucket_users.blob(f'{self.current_username}')
        content = user_blob.download_as_string().decode('utf-8').split('\n')[2]
        print(content)
        print("content\ngetHistory\n\n")
        content = content.replace('\'', '')
        return content.strip('][\'').split(', ')
    
    def add_to_history(self, page_name):
        user_blob = self.bucket_users.blob(f'{self.current_username}')
        content = user_blob.download_as_string().decode('utf-8').split('\n')
        
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')

        raw_log = content[2]
        raw_log = raw_log.replace('[', '')
        raw_log = raw_log.replace(']', '')
        raw_log = raw_log.replace('\'', '')
        raw_log = raw_log.split(', ')

        history = raw_log
        
        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history.append(page_name)
        history.append(timestamp)

        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
    
    def get_all_page_names(self):
        """
        Args: 
            Nothing
        Explain:
            Gets all markdown sub-pages from google cloud buckets
        Returns:
            List of sub-page names (List)
        """
        all_blobs = list(self.bucket_content.list_blobs())
        #Could add a feature where users upload their own content??

        page_names = []
        for blob in all_blobs:
            name = blob.name.split('.')
            if name[0] in self.sub_pages and name[-1] == 'md':
                page_names.append(name[0])

        page_names.sort()
        return page_names

    def get_wiki_page(self, page_name):
        """
        Args: A page name (Str)
        Explain: Converts a specific markdown file to html, 
                 adds the header, and stores that in local files.
        Returns: N/A
        """
        md_blob = self.bucket_content.blob(f'{page_name}.md')
        md_content = md_blob.download_as_string().decode('utf-8')
        html_content = markdown.markdown(md_content)
        
        return html_content

    def upload(self, content, filename):
        """
        Args: Contents of a file (IO), the filename (Str)
        Explain: Uploads a .md, .jpg, .jpeg or .png,
                 to a google cloud bucket (Content or Images)
        Returns: (Boolean)
        """
        file_end = filename.split(".")[-1].lower()
        #if filename.endswith('.md'):
        if file_end == "md":
            if not self.url_check(content, filename):
                return False
            content.seek(0)
            blob = self.bucket_content.blob(os.path.basename(filename))
        elif file_end == "jpeg" or file_end == "jpg" or file_end == "png":
            #elif filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
            blob = self.bucket_images.blob(os.path.basename(filename))
        else:
            return False

        blob.upload_from_file(content)
        return True

    def url_check(self, file_content, filename):
        """
        Args: Contents of a file (IO), the filename (Str)
        Explain: Checks if a .md file has valid links to the site
        Returns: (Boolean)
        """
        content = str(file_content.read())
        check_urls = re.findall(r'\[(.*?)\]\((.*?)\)', content)

        for url in check_urls:
            if url[1][1:] in self.all_pages:
                pass
            elif url[1][2:] in self.all_pages:
                pass
            else:
                return False
        return True

    def get_image(self):
        """
        Args: Nothing
        Explain: Retrieves image urls from google cloud 
                 buckets (Content and Images), excluding authors.
        Returns: List of image urls (List)
        """
        #storage_client = storage.Client()
        #bucket = self.bucket_content
        blobs = list(self.bucket_content.list_blobs())
        blobs = list(self.bucket_images.list_blobs())
        images_lst = []

        for blob in blobs:
            if blob.name.startswith("[Author]"):
                continue
            blob_img = blob.public_url
            images_lst.append(blob_img)

        images_lst.sort()
        return images_lst

    def get_about(self):
        """
        Args: Nothing
        Explain: Retrieves image urls from google cloud 
                 buckets (Images), only authors.
        Returns: List of image urls and author names (List)
        """
        storage_client = storage.Client()
        blobs = list(self.bucket_images.list_blobs())
        images_lst = []
        for blob in blobs:
            if blob.name.startswith("[Author]"):
                blob_img = blob.public_url
                name = blob.name.split(",")[1]
                images_lst.append((blob_img, name))
            else:
                continue

        images_lst.sort()
        return images_lst

    def sign_up(self, user_info):
        """
        Args: A users info (Dict(name, username, password))
        Explain: Adds user to GCB (users), if they dont 
                 already exist and allows login.
        Returns: (Boolean), A user's name or empty (str)
        """
        user_name = user_info['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')

        if user_blob.exists():
            return False, ''

        user_pass = user_info['password']
        name = user_info['name']

        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history = ["Account Began", timestamp]


        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())
        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(encoded, salt)

        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
        self.current_username = user_name
        return True, name

    def sign_in(self, user_check):
        """
        Args: Users sign-in info ( Dict(username, password) )
        Explain: Checks if an existing user entered the correct 
                 credentials and allows for login.
        Returns: (Boolean), A user's name or empty (str)
        """
        user_name = user_check['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')

        if not user_blob.exists():
            return False, ''

        content = user_blob.download_as_string().decode('utf-8').split('\n')
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')

        raw_log = content[2]
        raw_log = raw_log.replace('[', '')
        raw_log = raw_log.replace(']', '')
        raw_log = raw_log.replace('\'', '')
        raw_log = raw_log.split(', ')

        history = raw_log
        
        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history.append("Logged In")
        history.append(timestamp)

        user_pass = user_check['password']
        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())

        if not bcrypt.checkpw(encoded, hash_pass):
            return False, ''

        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
        self.current_username = user_name        

        return True, name
