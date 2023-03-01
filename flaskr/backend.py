from google.cloud import storage
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from bcrypt import encode, gensalt, hashpw, checkpw

# TODO(Project 1): Implement Backend according to the requirements.
class Backend:
    
    def __init__(self, app):
        #Used for logging in/out
        self.app = app
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        #Buckets
        storage_client = storage.Client()
        self.bucket_content = storage_client.bucket('minorbugs_content')
        self.bucket_users = storage_client.bucket('minorbugs_users')
    
    def get_wiki_page(self, name):
        raise NotImplementedError

    def get_all_page_names(self):
        raise NotImplementedError

    def upload(self, content):
        raise NotImplementedError
    
    def sign_up(self, user_info):
        raise NotImplementedError

    def sign_in(self, user_check):
        user_name = user_check['username']
        user_blob = self.bucket_content.blob(f"{user_name}.txt")

        if not user_blob.exists():
            return (False,)
        
        user_pass = user_check['password']
        
        content = user_blob.download_as_string().split('\n')
        name = content[0]
        hash_pass = content[1]

        if not checkpw(user_pass, hash_pass):
            return (False,)

        return (True, f'{user_name}', name)

    def get_image(self):
        raise NotImplementedError


"""

    user_name = user_info['username']
    user_blob = self.bucket_content.blob(f"{user_name}.txt' ")

    if user_blob.exists():
        return (False,)

    name = user_info['name']
    user_pass = user_info['username']

    encoded = user_pass.encode()
    salt = gensalt()
    hash_pass = hashpw(encoded, salt)

    user_blob.upload_from_string(f"{name}\n{hash_pass}")
    return (True, user_name)

    def write(self, bucket_name, blob_name, content):
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            with blob.open('w') as w:
                w.write()

            raise NotImplementedError
"""
