from flask import abort, render_template
from flaskr.pages import make_endpoints
from unittest.mock import MagicMock, Mock, patch, ANY
from flaskr import create_app
from werkzeug.datastructures import FileStorage
import pytest
from google.cloud import storage
import os


# See https://flask.palletsprojects.com/en/2.2.x/testing/
# for more info on testing

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


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200  #This check that the connection to homepage is good
    assert b"Music Theory Wiki" in resp.data  #This check if the cilent can grabs the data within the homepage
    assert b"<h1>" in resp.data


def test_pages(client, mock_backend):
    mock_backend.get_all_page_names.return_value = ["test_page0", "test_page1"]
    resp = client.get("/pages")

    assert resp.status_code == 200
    assert b"<a href=\"/pages/test_page0\">test_page0</a>" in resp.data
    assert b"<a href=\"/pages/test_page1\">test_page1</a>" in resp.data

def test_pages_next(client, mock_backend):
    test_data = ("Test Content", "Test Summary")
    mock_backend.get_wiki_page.return_value = test_data
    
    resp = client.get("/pages/sub_pages")

    assert resp.status_code == 200
    assert b'Test Content' in resp.data
    assert b'Test Summary' in resp.data


def test_about(client, mock_backend):
    "Explain: test about page "
    mock_backend.get_about.return_value = [("test_uri0", "test_name0"),
                                           ("test_uri1", "test_name1")]
    resp = client.get("/about")
    assert resp.status_code == 200
    assert b"<h2>test_name0</h2>" in resp.data
    assert b"<h2>test_name1</h2>" in resp.data
    assert b"<img src=\"test_uri0\" alt=\"test_uri0\"" in resp.data
    assert b"<img src=\"test_uri1\" alt=\"test_uri1\"" in resp.data


def test_welcome(client):
    """Explain: Test if a person can access welcome page"""
    resp = client.get("/welcome")
    assert resp.status_code == 200
    assert b"Welcome" in resp.data

def test_get_login(client):
    """Explain: Test if a person can access login page"""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"<h1>Login</h1>" in resp.data

def test_comments_upload(client,mock_backend):
    """Explain: Test if a person can post a comment"""
    resp = client.post("/comments", data = {"comment": "helloworld", "hidden":"sandy"})
    mock_backend.upload_comment.assert_called_once()

def test_comments_view(client,mock_backend):
    """Explain: Test if a person can access comment page"""
    resp = client.get("/comments")
    assert resp.status_code ==200
    assert b"Post your comment here!" in resp.data


@patch("uuid.uuid4")
def test_auth_login_success(mock_uuid, client, mock_backend):
    """Explain: Test if login works"""
    mock_uuid.return_value = "1234"
    mock_backend.sign_in.return_value = (True, "Test Name")
    resp = client.post("/auth_login",
                       data={
                           "Username": "U",
                           "Password": "P"
                       },
                       follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome Test Name" in resp.data


def test_auth_login_fail(client, mock_backend):
    """Explain: Test if login fails"""
    mock_backend.sign_in.return_value = (False, "Test Name")
    resp = client.post("/auth_login", data={"Username": "U", "Password": "P"})
    assert resp.status_code == 200
    assert b"Incorrect Username and/or Password" in resp.data


def test_logout(client, mock_backend):
    """Explain: Test if a person can log out"""
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Music Theory Wiki" in resp.data


def test_upload_page(client):
    """Explain: Test if a person can access upload page """
    resp = client.get("/upload")
    assert resp.status_code == 200
    assert b"*Only accepts .jpg, .png" in resp.data


def test_upload_success(client, mock_backend):
    """Explain: Test if upload works"""
    file_ = FileStorage(filename="test_dir/test_file.md",
                        content_type="text/markdown")
    resp = client.post("/upload", data={"upload": file_}, follow_redirects=True)

    mock_backend.upload.assert_called_once_with(ANY, "test_file.md")
    assert resp.status_code == 200
    assert b"Music Theory Wiki" in resp.data


def test_upload_fail(client):
    """Explain: Test if upload fails"""
    file_ = FileStorage(filename="test_dir/test_file.bad")
    resp = client.post("/upload", data={"upload": file_}, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Incorrect File Type" in resp.data


def test_get_signup(client):
    """Explain: Test if a person can access signup page"""
    resp = client.get("/signup")
    assert resp.status_code == 200
    assert b"<h1>Sign Up</h1>" in resp.data

# if file format is not (.jpg) (.jpeg) (.png) or (.md) assert error
def test_get_about(client):
    """Explain: Test if a person can access about page"""
    resp = client.get("/about")
    assert resp.status_code == 200  #This check that the connection to about is good
    assert b"Your Authors" in resp.data  #This check if the cilent can grabs the data within about

def test_get_page_summary(client, mock_backend):
    """Explain: Test if a person can get summary from get_wiki_page"""
    mock_backend.get_wiki_page.return_value=("Chord is a group of notes","a group of notes")
    resp = client.get("/pages/sub_pages")
    assert resp.status_code == 200  #This check that the connection to about is good
    assert b"a group of notes" in resp.data

def test_get_page_summary_None(client, mock_backend):
    """Explain: Test if a person can get summary from get_wiki_page if it is None"""
    test_main = "Chord is a group of notes"
    main_len=len(test_main)
    mock_backend.get_wiki_page.return_value=("Chord is a group of notes",None)
    resp = client.get("/pages/sub_pages")
    str_resp = resp.data.decode("utf-8")[:-main_len]
     
    assert resp.status_code == 200  #This check that the connection to about is good
    assert "Chord" not in str_resp
    assert "Chord is a group of notes" not in str_resp

# def test_pages(client):
#     resp = client.get("/pages")
#     assert resp.status_code == 200  #This check that the connection to pages is good
#     assert b"All Pages" in resp.data
#     assert b"Sub-Pages" in resp.data


@patch("uuid.uuid4")
def test_signup_success(mock_uuid, login_client, mock_backend):
    """Explain: Test if the page when signup is successful displays"""
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
    assert b"Welcome Test Name" in resp.data

def test_get_welcome(client, mock_backend):
    """ExplainL Test if a person can access welcome page"""
    resp = client.get("/welcome")
    assert resp.status_code == 200  #This check that the connection to welcome is good
    assert b"Welcome" in resp.data  #This check if the cilent can grabs the data within welcome

# user vincent username is username and password is password

'''
This would be my test for the update but I'm not sure how I could mock a logged in user
# def test_history(client):
#     resp = client.get("/history")
#     assert resp.status_code == 200  #This check that the connection to about is good
#     assert b"History" in resp.data  #This check if the cilent can grabs the data within about
'''
def test_signup_fail(client, mock_backend):
    """Explain: Test if the page when signup doesn't work displays"""
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
    """Example: Check if get_image from backend works"""
    mock_backend.get_image.return_value = ["pic0", "pic1"]
    resp = client.get("/images")
    assert resp.status_code == 200
    assert b"src=\"pic0\" alt=\"pic0\"" in resp.data
    assert b"src=\"pic1\" alt=\"pic1\"" in resp.data


def test_invalid_method(client, mock_backend):
    """Example: Test if a user cannot access a method"""
    mock_backend.get_image = lambda: abort(405)
    resp = client.get("/images", follow_redirects=True)
    assert resp.status_code == 405
    assert b"<a href=\"/\">/</a>" in resp.data


def test_page_sort_alpha(client, mock_backend):
    """Example: Test if get_all_page_name sorts alphabetically """
    mock_backend.get_all_page_names.return_value = ['a_test', 'b_test', 'c_test']
    resp = client.get('/pages', query_string={'sort_by': 'Alphabetical'})
    
    assert resp.status_code == 200
    str_data = resp.data.decode('utf-8')
    a_idx, b_idx, c_idx = str_data.find('a_test'), str_data.find('b_test'), str_data.find('c_test')
    assert -1 < a_idx < b_idx < c_idx


def test_page_sort_pop(client, mock_backend):
    """Example: Test if sort_by_popularity sorts by popularity """
    mock_backend.page_sort_by_popularity.return_value = ['3_test', '2_test', '1_test']
    resp = client.get('/pages', query_string={'sort_by': 'Popularity'})

    assert resp.status_code == 200
    str_data = resp.data.decode('utf-8')
    print(str_data)
    idx_3, idx_2, idx_1 = str_data.find('3_test'), str_data.find('2_test'), str_data.find('1_test')
    assert -1 < idx_3 < idx_2 < idx_1
