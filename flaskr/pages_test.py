from flaskr.backend import Backend
from flaskr import backend
from unittest.mock import MagicMock, patch
from flaskr import create_app
import pytest


class storage_client_mock:
    def __init__(self, app_mock=None):
        pass

    def bucket(self, bucket_name):
      return bucket_object(bucket_name)
  
    
class bucket_object:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.blobz = []

    def list_blobs(self):
        return self.blobz
        
    def blob(self, blob_name, user_info=False):
        temp_blob = blob_object(blob_name, user_info)
        self.blobz.append(temp_blob)
        return temp_blob


class blob_object:
    def __init__(self, blob_name, user_info = False):
        self.name = blob_name
        self.info = user_info

    def exists(self):
        if self.info:
            return True
        else:
            return False

    def set_public_url(self, url_name):
        self.public_url = url_name

    def upload_from_string(self, content):
        self.string_content = content

    def download_as_string(self, content):
        return self.string_content

    def upload_from_file(self, content):
        self.file_content = content

    def download_to_filename(self, file_path):
        return self.file_content


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





# See https://flask.palletsprojects.com/en/2.2.x/testing/ 
# for more info on testing
@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
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
    assert resp.status_code == 200 #This check that the connection to homepage is good
    assert b"Music Theory Wiki" in resp.data #This check if the cilent can grabs the data within the homepage
    assert b"<h1>" in resp.data

# TODO(Project 1): Write tests for other routes.
def test_auth_login_failed(self,user_blob,user_name,password):
    user_check={"name":"Dr.Otter","username":"Otter123","password":"Wood"}
    #for blob in client.bucket("minorbugs_users").blobs:
        #if blob.username==user_check["username"]:
            #if blob.password!=user_check["password"]:
                #assert 5<2
    #assert 1==1 
    #if user name not in blob list assert error
    #if password not equal blob password assert error
    pass
    
def test_auth_login_sucesss(client):
    user_check={"name":"vincent","username":"username","password":"password"}
    #for blob in client.bucket("minorbugs_users").blobs:
        #if blob.username==user_check["username"]:
            #if blob.password!=user_check["password"]:
                #assert 5<2
    #assert 1==1   

    #if user name not in blob list assert error
    #if password not equal blob password assert error
    pass
def test_logout(client):
    #test is_authenticated ==None else assert error
    pass
def test_sign_up_success():
    user_check={"name":"Graves","username":"deadman","password":"walking"}
    #for blob in client.bucket("minorbugs_users").blobs:
        #if blob.username==user_check["username"]:
            #assert 5<2
    
    # if username is in blob list else assert error
    pass
def test_sign_up_failed():
    user_check={"name":"vincent","username":"username","password":"password"}
    #for blob in client.bucket("minorbugs_users").blobs:
        #if blob.username==user_check["username"]:
            #assert 5<2
    # if username is in blob list else assert error
    pass
def test_upload_failed(client):
    resp=client.get("/upload")

    assert resp.status_code ==200 #This check that the connection to upload is good
    # if file format is not (.jpg) (.jpeg) (.png) or (.md) assert error 
    
def test_upload_success(client):
    resp=client.get("/upload")
    assert resp.status_code ==200 #This check that the connection to upload is good
    # if file format is not (.jpg) (.jpeg) (.png) or (.md) assert error 
def test_get_about(client):
    resp=client.get("/about")
    assert resp.status_code ==200 #This check that the connection to about is good
    assert b"Your Authors" in resp.data #This check if the cilent can grabs the data within about
def test_pages(client):
    resp=client.get("/pages")
    assert resp.status_code ==200 #This check that the connection to pages is good
    assert b"All Pages" in resp.data
    assert b"Sub-Pages" in resp.data
def test_pages_next(client):
    resp=client.get("/pages/chord")
    assert resp.status_code ==200 #This check that the connection to a sub pages is good
    assert b"Chord" in resp.data
   
def test_get_welcome(client):
    resp=client.get("/welcome")
    user_check={"username":"username","password":"password"}
    #sign in user to use welcome
    assert resp.status_code ==401 #This check that the connection to welcome is good
    assert b"Welcome" in resp.data  #This check if the cilent can grabs the data within welcome
def test_get_login(client):
    resp=client.get("/login")
    assert resp.status_code ==200 #This check that the connection to login is good
    assert b"Login Page" in resp.data  #This check if the cilent can grabs the data within login
    assert b"Login" in resp.data 
def test_get_sign_up_success(client):
    resp=client.get("/signup")
    assert resp.status_code ==200 #This check that the connection to signup is good
    assert b"Signup Page" in resp.data  #This check if the cilent can grabs the data within signup
    assert b"Sign Up" in resp.data

# user vincent username is username and password is password