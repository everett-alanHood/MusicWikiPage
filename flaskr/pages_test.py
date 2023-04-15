from flaskr.pages import make_endpoints
from flaskr.backend import Backend
from flaskr import backend
from unittest.mock import MagicMock, patch
from flaskr import create_app
import pytest


### From Brian Noyama's test changes ###

@pytest.fixture
def mock_backend():
    mock_backend = MagicMock()
    # Set the initializer to return the same mock.
    mock_backend.return_value = mock_backend
    return mock_backend

@pytest.fixture
def app(mock_backend):
    app = create_app({
        'TESTING': True,
        'LOGIN_DISABLED': True,
    }, mock_backend)
    return app

########################################

# See https://flask.palletsprojects.com/en/2.2.x/testing/
# for more info on testing


@pytest.fixture
def client(app):
    return app.test_client()


def test_page_sort_alpha(client, mock_backend):
    mock_backend.get_all_page_names.return_value = ['a_test', 'b_test', 'c_test']
    resp = client.get('/pages', query_string={'sort_by': 'Alphabetical'})
    
    assert resp.status_code == 200
    str_data = resp.data.decode('utf-8')
    a_idx, b_idx, c_idx = str_data.find('a_test'), str_data.find('b_test'), str_data.find('c_test')
    assert -1 < a_idx < b_idx < c_idx


def test_page_sort_pop(client, mock_backend):
    mock_backend.page_sort_by_popularity.return_value = ['3_test', '2_test', '1_test']
    resp = client.get('/pages', query_string={'sort_by': 'Popularity'})
    
    assert resp.status_code == 200
    str_data = resp.data.decode('utf-8')
    print(str_data)
    idx_3, idx_2, idx_1 = str_data.find('3_test'), str_data.find('2_test'), str_data.find('1_test')
    assert -1 < idx_3 < idx_2 < idx_1
    


def test_home_page(client):
    resp = client.get("/")
    #@patchPage
    assert resp.status_code == 200  #This check that the connection to homepage is good
    assert b"Music Theory Wiki" in resp.data  #This check if the cilent can grabs the data within the homepage
    assert b"<h1>" in resp.data


# TODO(Project 1): Write tests for other routes.
def test_sign_up_success():
    # client = storage_client_mock()
    # bucket = client.bucket('users')
    # blob = bucket.blob('hi')

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

