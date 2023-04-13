from flaskr.pages import make_endpoints
from flaskr.backend import Backend
from flaskr import backend
from unittest.mock import MagicMock, patch
from flaskr import create_app
import pytest
from google.cloud import storage
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import tokenizer_from_json


class storage_client_mock:

    def __init__(self, app_mock=None):
        self.bucketz = dict()

    def list_buckets(self):
        return self.bucketz

    def bucket(self, bucket_name):
        if bucket_name in self.bucketz:
            return self.bucketz[bucket_name]

        temp_bucket = bucket_object(bucket_name)
        self.bucketz[bucket_name] = temp_bucket
        return temp_bucket


class bucket_object:

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.blobz = dict()

    def list_blobs(self):
        return self.blobz

    def blob(self, blob_name):
        blob_name = blob_name.lower()

        if blob_name in self.blobz:
            return self.blobz[blob_name]

        temp_blob = blob_object(blob_name)
        self.blobz[blob_name] = temp_blob
        return temp_blob

class blob_object:

    def __init__(self, blob_name):
        self.name = blob_name
        self.public_url = False
        self.uploaded = None

    def exists(self):
        if not self.public_url:
            return False
        else:
            return True

    def _set_public_url(self, url_name, *args, **kwargs):
        self.public_url = url_name

    def upload_from_string(self, content, *args, **kwargs):
        self.uploaded = True
        self.public_url = 'test/test.com'
        self.string_content = content

    def upload_from_file(self, content, *args, **kwargs):
        self.uploaded = True
        self.public_url = 'test/test.com'
        self.file_content = content

    def download_as_string(self, *args, **kwargs):
        if self.uploaded:
            return self.string_content.encode('utf-8')
        return 'This is a test string from download_as_string'.encode('utf-8')

    def download_to_filename(self, *args, **kwargs):
        if self.uploaded:
            return self.file_content
        return 'This is a test from download_to_filename'

    def open(self, *args, **kwargs):
        data = ['## The header',
                'This is the first line [test](test)',
                'The second line is important',
                'Third line is here',
                'Last line in data' ]

        return [line.encode('utf-8') for line in data]

class mock_model_load:

    def __init__ (self, *args, **kwargs):
        pass

    def predict(self, data, *args, **kwargs):
        return data[::-1]

def mock_tokenizer_from_json(*args, **kwargs):
    return mock_tokenizer()

class mock_tokenizer:
    
    def __init__(self, *args, **kwargs):
        pass

    def texts_to_sequences(self, data, *args, **kwargs):
        self.data = data
        return [1,2,3,4,5]
    
    def sequences_to_text(self, data, *args, **kwargs):
        return list(self.data)[::-1]

def load_user_mock(data):
    mock_user = User_mock(data)
    return mock_user

class User_mock:

    def __init__(self, name):
        self.name = name
        self.id = 10

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

class Flask_mock:

    def __init__(self, name):
        pass

def mock_function(mock_SC=True, mock_load_model=True, mock_token=True, length=1600):
    mocked = [storage_client_mock(), mock_model_load, mock_tokenizer_from_json, length]
    
    if not mock_SC:
        mocked[0] = storage.Client()
    if not mock_load_model:
        mocked[1] = load_model
    if not mock_token:
        mocked[2] = tokenizer_from_json

    return mocked

# See https://flask.palletsprojects.com/en/2.2.x/testing/
# for more info on testing
@pytest.fixture
def app():
    app = create_app({'TESTING': True,}, 
                      mocking=mock_function())
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def mock_blob():
    pass


# TODO(Checkpoint (groups of 4 only) Requirement 4): Change test to
# match the changes made in the other Checkpoint Requirements.
def test_home_page(client):
    resp = client.get("/")
    #@patchPage
    assert resp.status_code == 200  #This check that the connection to homepage is good
    assert b"Music Theory Wiki" in resp.data  #This check if the cilent can grabs the data within the homepage
    assert b"<h1>" in resp.data


# TODO(Project 1): Write tests for other routes.
def test_sign_up_success():
    client = storage_client_mock()
    bucket = client.bucket('users')
    blob = bucket.blob('hi')

    user_check = {"name": "test", "username": "hell", "password": "testhello"}


def test_sign_up_failed():
    user_check = {
        "name": "vincent",
        "username": "username",
        "password": "password"
    }
    #for blob in client.bucket("minorbugs_users").blobs:
    #if blob.username==user_check["username"]:
    #assert 5<2
    # if username is in blob list else assert error
    pass


def test_logout(client):
    #test is_authenticated ==None else assert error
    pass


# def test_auth_login_failed(self, user_blob, user_name, password):
#     pass


def test_auth_login_sucesss(client):
    user_check = {
        "name": "vincent",
        "username": "username",
        "password": "password"
    }
    #for blob in client.bucket("minorbugs_users").blobs:
    #if blob.username==user_check["username"]:
    #if blob.password!=user_check["password"]:
    #assert 5<2
    #assert 1==1

    #if user name not in blob list assert error
    #if password not equal blob password assert error
    pass


# def test_upload_failed(client):
#     resp = client.get("/upload")

#     assert resp.status_code == 200  #This check that the connection to upload is good
#     # if file format is not (.jpg) (.jpeg) (.png) or (.md) assert error


# def test_upload_success(client):
#     resp = client.get("/upload")
#     assert resp.status_code == 200  #This check that the connection to upload is good


    # if file format is not (.jpg) (.jpeg) (.png) or (.md) assert error
def test_get_about(client):
    resp = client.get("/about")
    assert resp.status_code == 200  #This check that the connection to about is good
    assert b"Your Authors" in resp.data  #This check if the cilent can grabs the data within about


# def test_pages(client):
#     resp = client.get("/pages")
#     assert resp.status_code == 200  #This check that the connection to pages is good
#     assert b"All Pages" in resp.data
#     assert b"Sub-Pages" in resp.data


# def test_pages_next(client):
#     resp = client.get("/pages/chord")
#     assert resp.status_code == 200  #This check that the connection to a sub pages is good
#     assert b"Chord" in resp.data


# def test_get_welcome(client):
#     resp = client.get("/welcome")
#     user_check = {"username": "username", "password": "password"}
#     #sign in user to use welcome
#     assert resp.status_code == 401  #This check that the connection to welcome is good
#     assert b"Welcome" in resp.data  #This check if the cilent can grabs the data within welcome


# user vincent username is username and password is password
