from flask import abort, render_template
from flaskr.pages import make_endpoints
from unittest.mock import MagicMock, Mock, patch, ANY
from flaskr import create_app
from werkzeug.datastructures import FileStorage
import pytest
import flask, os

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

    
@pytest.fixture
def login_app(mock_backend):
    app = create_app({
        'TESTING': True,
    }, mock_backend)
    return app


@pytest.fixture
def login_client(login_app):
    return login_app.test_client()
    

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
    assert resp.status_code == 200  #This check that the connection to homepage is good
    assert b"Music Theory Wiki" in resp.data  #This check if the cilent can grabs the data within the homepage
    assert b"<h1>" in resp.data


# TODO(Project 1): Write tests for other routes.
# def test_sign_up_success():
    # client = storage_client_mock()
    # bucket = client.bucket('users')
    # blob = bucket.blob('hi')

def test_pages(client, mock_backend):
    mock_backend.get_all_page_names.return_value = ["test_page0", "test_page1"]
    resp = client.get("/pages")

    assert resp.status_code == 200
    assert b"<a href=\"/pages/test_page0\">test_page0</a>" in resp.data
    assert b"<a href=\"/pages/test_page1\">test_page1</a>" in resp.data


@patch("flaskr.pages.render_template")
def test_pages_next(mock_render, client, mock_backend):
    mock_backend.get_wiki_page.return_value = "Test Content"
    mock_render.return_value = "Test Content"

    resp = client.get("/pages/test")

    mock_render.assert_called_once_with("test.html", content="Test Content")
    assert resp.status_code == 200
    assert b"Test Content" == resp.data


def test_about(client, mock_backend):
    mock_backend.get_about.return_value = [("test_uri0", "test_name0"),
                                           ("test_uri1", "test_name1")]
    resp = client.get("/about")
    assert resp.status_code == 200
    assert b"<h2>test_name0</h2>" in resp.data
    assert b"<h2>test_name1</h2>" in resp.data
    assert b"<img src=\"test_uri0\" alt=\"test_uri0\"" in resp.data
    assert b"<img src=\"test_uri1\" alt=\"test_uri1\"" in resp.data


def test_welcome(client):
    resp = client.get("/welcome")
    assert resp.status_code == 200
    assert b"Welcome" in resp.data


def test_get_login(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"<h1>Login</h1>" in resp.data


@patch("uuid.uuid4")
def test_auth_login_success(mock_uuid, client, mock_backend):
    mock_uuid.return_value = "1234"
    mock_backend.sign_in.return_value = (True, "Test Name")
    resp = client.post("/auth_login",
                       data={
                           "Username": "U",
                           "Password": "P"
                       },
                       follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome 1234" in resp.data


def test_auth_login_fail(client, mock_backend):
    mock_backend.sign_in.return_value = (False, "Test Name")
    resp = client.post("/auth_login", data={"Username": "U", "Password": "P"})
    assert resp.status_code == 200
    assert b"Incorrect Username and/or Password" in resp.data


def test_logout(client, mock_backend):
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Music Theory Wiki" in resp.data


def test_upload_page(client):
    resp = client.get("/upload")
    assert resp.status_code == 200
    assert b"*Only accepts .jpg, .png" in resp.data


def test_upload_success(client, mock_backend):
    file_ = FileStorage(filename="test_dir/test_file.md",
                        content_type="text/markdown")
    resp = client.post("/upload", data={"upload": file_}, follow_redirects=True)

    mock_backend.upload.assert_called_once_with(ANY, "test_file.md")
    assert resp.status_code == 200
    assert b"Music Theory Wiki" in resp.data


def test_upload_fail(client):
    file_ = FileStorage(filename="test_dir/test_file.bad")
    resp = client.post("/upload", data={"upload": file_}, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Incorrect File Type" in resp.data


def test_get_signup(client):
    resp = client.get("/signup")
    assert resp.status_code == 200
    assert b"<h1>Sign Up</h1>" in resp.data


@patch("uuid.uuid4")
def test_signup_success(mock_uuid, login_client, mock_backend):
    mock_backend.sign_up.return_value = (True, "Test Name")
    mock_uuid.return_value = "1234"
    resp = login_client.post("/auth_signup",
                             data={
                                 "Name": "Test Name",
                                 "Username": "test_user_name",
                                 "Password": "test_password",
                             },
                             follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome 1234" in resp.data


def test_signup_fail(client, mock_backend):
    mock_backend.sign_up.return_value = (False, "Test Name")
    resp = client.post("/auth_signup",
                       data={
                           "Name": "Test Name",
                           "Username": "test_user_name",
                           "Password": "test_password",
                       })

    assert resp.status_code == 200
    assert b"User already exists" in resp.data


def test_get_allimages(client, mock_backend):
    mock_backend.get_image.return_value = ["pic0", "pic1"]
    resp = client.get("/images")
    assert resp.status_code == 200
    assert b"src=\"pic0\" alt=\"pic0\"" in resp.data
    assert b"src=\"pic1\" alt=\"pic1\"" in resp.data


def test_invalid_method(client, mock_backend):
    mock_backend.get_image = lambda: abort(405)
    resp = client.get("/images", follow_redirects=True)
    assert resp.status_code == 405
    assert b"<a href=\"/\">/</a>" in resp.data
