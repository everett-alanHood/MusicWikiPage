from google.cloud import storage
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
# from flaskr.__init__ import create_app

# TODO(Project 1): Implement Backend according to the requirements.
class Backend:
    def __init__(self):
        self.app = Flask(__name__) # create_app()
        self.app.secret_key = 'test_key'
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)

        raise NotImplementedError
    
    def get_wiki_page(self, name):
        raise NotImplementedError

    def get_all_page_names(self):
        raise NotImplementedError

    def upload(self, content):
        raise NotImplementedError
    
    def sign_up(self, user_info):
        raise NotImplementedError

    def sign_in(self, user_check):

        raise NotImplementedError

    def get_image(self):
        raise NotImplementedError


"""
    Creates client
    storage_client = storage.Client()

    Names for buckets
    content_name = 'minorbugs_content'
    users_name = 'minorbugs_users'

    Gets buckets
    bucket_content = storage_client.get_bucket(content_name)
    bucket_users = storage_client.get_bucket(users_name)


    def write(self, bucket_name, blob_name, content):
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            with blob.open('w') as w:
                w.write()

            raise NotImplementedError
"""
