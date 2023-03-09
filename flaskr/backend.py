from google.cloud import storage
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
#Hasing password
import bcrypt #gensalt, hashpw, checkpw
import base64
import hashlib
import os
# from markdown import markdown
import markdown
import re


# TODO(Project 1): Implement Backend according to the requirements.
class Backend:
    
    def __init__(self, app):
        #Used for logging in/out
        test_app = Flask(__name__)
        self.login_manager = LoginManager()
        self.login_manager.init_app(test_app)
        #Buckets
        storage_client = storage.Client()
        self.bucket_content = storage_client.bucket('minorbugs_content')
        self.bucket_users = storage_client.bucket('minorbugs_users')
        self.bucket_images = storage_client.bucket('minorbugs_images')
        #page urls
        self.pages = {'/', 'pages', 'about', 'welcome', 'login', 'logout', 'upload', 'signup', 'images'}
        self.sub_pages = {'chord', 'harmony', 'pitch', 'rhythm', 'melody', 'scales', 'timbre', 'form', 'dynamics', 'texture'}
        self.all_pages = self.pages | self.sub_pages

    def get_all_page_names(self):
        all_blobs = list(self.bucket_content.list_blobs())
        #Could add a feature where users can upload their own content??

        page_names = []
        for blob in all_blobs:
            name = blob.name.split('.')
            if name[0] in self.sub_pages and name[-1] == 'md':
                page_names.append(name[0])
        
        page_names.sort()
        return page_names

    def get_wiki_page(self, page_name):
        md_blob = self.bucket_content.blob(f'{page_name}.md')

        md_path = f'flaskr/temp_markdown/{page_name}.md'
        html_path = f'flaskr/templates/{page_name}.html'
        
        md_blob.download_to_filename(md_path)
        markdown.markdownFromFile(input=md_path, output=html_path, encoding='utf-8')
        
        with open(html_path, 'r') as f:
            html_content = f.read()           
        
        html_header = "{% include 'header.html' %}" + html_content
    
        with open(html_path, 'w') as f:
            f.write(html_header)
        
        # md_content = md_blob.download_as_string().decode('utf-8')
        # html_content = markdown(md_content)
        # return html_content

    def upload(self, content, filename):
        print(os.path.basename(content.name))

        if filename.endswith('.md'):
            if not self.url_check(content, filename):
                return False 
            content.seek(0)
            blob = self.bucket_content.blob(os.path.basename(filename))
        else:
            blob = self.bucket_images.blob(os.path.basename(filename))
        
        blob.upload_from_file(content)
        return True

    def url_check(self, file_content, filename):
        content = str(file_content.read())
        check_urls = re.findall(r'\[(.*?)\]\((.*?)\)', content)

        for url in check_urls:
            if url[1][1:] in self.all_pages:pass
            elif url[1][2:] in self.all_pages:pass
            else:
                return False
        return True

    def get_image(self):
        storage_client = storage.Client()
        bucket = self.bucket_content
        blobs = storage_client.list_blobs("minorbugs_content")
        blobs = storage_client.list_blobs("minorbugs_images")
        images_lst = []

        for blob in blobs:
            if blob.name.startswith("[Author]"):
                continue
            blob_img = blob.public_url
            images_lst.append(blob_img)
        
        return images_lst
    
    def get_about(self):
        storage_client = storage.Client()
        blobs = storage_client.list_blobs("minorbugs_images")
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
        user_name = user_info['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')

        if user_blob.exists():
            return False, 0

        user_pass = user_info['password']
        name = user_info['name']

        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())
        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(encoded, salt)

        user_blob.upload_from_string(f"{name}\n{hash_pass}")
        return True, name

    def sign_in(self, user_check):
        user_name = user_check['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')
        
        if not user_blob.exists():
            return False, 0
        
        content = user_blob.download_as_string().decode('utf-8').split('\n')
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')

        user_pass = user_check['password']
        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())

        if not bcrypt.checkpw(encoded, hash_pass):
            return False, 0

        return True, name


"""
    #Sign up
    user_name = user_info['username']
    user_blob = self.bucket_content.blob(f"{user_name}.txt' ")

    if user_blob.exists():
        return (False,)

    name = user_info['name']
    user_pass = user_info['username']

    encoded = base64.b64encode(hashlib.sha256(user_pass.encode()).digest()
    salt = bcrypt.gensalt()
    hash_pass = hashpw(encoded, salt)

    user_blob.upload_from_string(f"{name}\n{hash_pass}")
    return (True, user_name)



    #Writing to file
    def write(self, bucket_name, blob_name, content):
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            with blob.open('w') as w:
                w.write()

            raise NotImplementedError
"""
