from flaskr.backend import Backend
from unittest.mock import MagicMock, patch
import pytest
@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
    })
    return app

@pytest.fixture
def page_name():
    name = "chord"
    return name
@pytest.fixture
def client(app):
    return app.test_client()
@pytest.fixture
def file_failed():
    file = MagicMock()
    file.endswith.return_value = ".txt"
    file.name.return_value = "text.txt"
    file.name.endswith.return_value = False
    file.endswith = lambda x: file.name.endswith(x)
    file.read.return_value = "text in text"


    return file

@pytest.fixture
def file_success():
    file = MagicMock()
    file.return_value = "Text from the start"
    file.endswith.return_value = True
    file.name.return_value = "test_sucess.md"
    file.name.endswith(".md").return_value = False
    file.name.endswith(".jpg").return_value = True
    file.read.return_value = "File Sucess"
    return file

@pytest.fixture
def valid_user():
    user_info = {}
    user_info['name'] = "Everett-Alan"
    user_info['username'] = "tim3line"
    user_info['password'] = "su4wirf-"
    return user_info

@pytest.fixture
def invalid_user():
    user_info = {}
    user_info['username'] = "invalid_name"
    user_info['username'] = "invalid_username"
    user_info['password'] = "invalid_password"
    return user_info

# TODO(Project 1): Write tests for Backend methods.
def test_sign_in_failed(valid_user,invalid_user):
    be = Backend(app)
    valid_user['password'] = "somethingElse"
    incorrect_password = be.sign_in(valid_user)
    invalid_user['username'] = "somethingElse"
    unknown_user = be.sign_in(invalid_user)
    assert incorrect_password[0] == False and unknown_user[0] == False
    
def test_sign_in_sucesss(valid_user):
    be = Backend(app)
    result = be.sign_in(valid_user)
    assert result[0] == True

def test_sign_up_failed(valid_user):
    be = Backend(app)
    known_user = be.sign_up(valid_user)
    assert known_user[0] == False

def test_sign_up_success(invalid_user):
    #TODO doesn't sign in the new user correctly
    be = Backend(app)
    unknown_user = be.sign_up(invalid_user)
    assert unknown_user[0] == True

def test_upload_failed(file_failed):
    be = Backend(app)
    val = be.upload(file_failed,file_failed.name)
    assert val == False
def test_upload_sucess(file_success):
    be = Backend(app)
    with patch.object(be, 'upload', return_value=True) as magic_upload:
        val = be.upload(file_success, file_success.name)
    assert val == True

def test_get_all_pages_names():
    be = Backend(app)
    names = be.get_all_page_names()
    n = ['chord', 'dynamics', 'form', 'harmony', 'melody', 'pitch', 'rhythm', 'scales', 'test_url', 'texture', 'timbre']
    assert n[3] in names

def test_get_wiki_page(page_name):
    be = Backend(app)
    page = be.get_wiki_page(page_name)
    file = open("flaskr/templates/%s.html" % page_name)
    assert len(file.read().split()) > 0

def test_get_image():
    images = 'https://storage.googleapis.com/minorbugs_images/Mozart.jpg'
    be = Backend(app)
    backend_images = be.get_image()
    assert images in backend_images
#test username:test password:test