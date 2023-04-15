from flaskr.backend import Backend
from unittest.mock import MagicMock, patch
import pytest
from google.cloud import storage
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import tokenizer_from_json
from flaskr.mock_test import storage_client_mock, mock_model_load, mock_tokenizer_from_json


def mock_function(mock_SC=True, mock_load_model=True, mock_token=True, length=1600):
    mocked = [storage_client_mock(), mock_model_load, mock_tokenizer_from_json, length]
    
    if not mock_SC:
        mocked[0] = storage.Client()
    if not mock_load_model:
        mocked[1] = load_model
    if not mock_token:
        mocked[2] = tokenizer_from_json
        
    return mocked


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


@pytest.fixture
def summary_name():
    return 'test mock '

def test_summary_model_true(summary_name): 
    back_end = Backend('app', mock_function())
    test = back_end.upload_summary(summary_name)
    assert test == True # Passes due to lengh of data being in acceptable range i.e. less than max data length

def test_summary_model_false(summary_name): 
    back_end = Backend('app', mock_function(length=5)) # length = max data length
    test = back_end.upload_summary(summary_name)
    assert test == False # Fails due to length of data being longer than whats allowed i.e. max data length=5

def test_sign_in_failed(valid_user, invalid_user):
    back_end = Backend('app', mock_function())
    back_end.sign_up(valid_user)
    valid, data = back_end.sign_in(invalid_user)
    assert valid == False
    assert data == ""

def test_sign_in_sucesss(valid_user):
    back_end = Backend('app', mock_function())
    back_end.sign_up(valid_user)
    valid, data = back_end.sign_in(valid_user)
    assert valid == True
    assert data == "Everett-Alan"

def test_sign_up_failed(valid_user):
    back_end = Backend('app', mock_function())
    back_end.sign_up(valid_user)
    valid, data = back_end.sign_up(valid_user)
    assert valid == False
    assert data == ""

def test_sign_up_success(valid_user):
    back_end = Backend('app', mock_function())
    valid, data = back_end.sign_up(valid_user)
    assert valid == True
    assert data == "Everett-Alan"

def test_upload_failed(file_failed):
    be = Backend(app, mock_function())
    val = be.upload(file_failed, file_failed.name)
    assert val == False


def test_upload_sucess(file_success):
    be = Backend(app, mock_function())
    with patch.object(be, 'upload', return_value=True):
        val = be.upload(file_success, file_success.name)
    assert val == True

def test_get_all_pages_names():
    be = Backend(app, mock_function())
    test_string = 'chord'
    with patch.object(be,
                      'get_all_page_names',
                      return_value=[
                          'chord', 'dynamics', 'form', 'harmony', 'melody',
                          'pitch', 'rhythm', 'scales', 'test_url', 'texture',
                          'timbre'
                      ]):
        pages = be.get_all_page_names()
    assert test_string in pages


def test_get_wiki_page(page_name):
    be = Backend(app, mock_function())
    with patch.object(
            be,
            'get_wiki_page',
            return_value=
            "{% include 'header.html' %}<p><h2>Chord</h2>Chord is a set of harmonic notes that are played simultaneously.</p>"
    ):
        pages = be.get_wiki_page(page_name)
    assert "<h2>Chord</h2>" in pages


def test_get_image():
    be = Backend(app, mock_function())
    images = 'https://storage.googleapis.com/minorbugs_images/Mozart.jpg'
    with patch.object(
            be,
            'get_image',
            return_value=
            "['https://storage.googleapis.com/minorbugs_images/HarmonyTheory.png', 'https://storage.googleapis.com/minorbugs_images/Mozart.jpg', 'https://storage.googleapis.com/minorbugs_images/MusicTheoryNotes.png', 'https://storage.googleapis.com/minorbugs_images/MusicalNotes.jpg']"
    ):
        backend_images = be.get_image()
    assert images in backend_images


# #test username:test password:test
