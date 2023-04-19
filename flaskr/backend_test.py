from flaskr.backend import Backend
from unittest.mock import MagicMock, patch
import pytest
from google.cloud import storage
from flaskr.mock_test import storage_client_mock, mock_model_load, mock_tokenizer_from_json, blob_object


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
def comment_success():
    file = MagicMock()
    file.return_value = "Text from the start"
    file.endswith.return_value = True
    file.name.return_value = "1680980576.6452136:sandy"
    file.read.return_value = "Hello World"
    return file


@pytest.fixture
def comment_failed():
    file = MagicMock()
    file.return_value = "Text from the start"
    file.endswith.return_value = True
    file.name.return_value = "1680980576.6452136:sandy"
    file.read.return_value = ""
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

def mock_function(mock_SC=True, mock_SC_blobs=dict(), length=1600):
    mocked = [None, mock_model_load, mock_tokenizer_from_json, length]
    
    if not mock_SC:
        mocked[0] = storage.Client()
    else:
        mocked[0] = storage_client_mock(mock_SC_blobs)
        
    return mocked


@pytest.fixture
def summary_name():
    return 'test_mock '

@pytest.fixture
def summary_lst_data():
    summary_data = ['## The header',
                    'This is the first line [test](test)',
                    'The second line is important',
                    'Third line is here',
                    'Last line in data' ]
    return summary_data

def summary_model_pass(summary_name, summary_lst_data): 
    # Passes due to lengh of data being in acceptable range 
    # i.e. less than max data length
    test_data = {summary_name : summary_lst_data}

    mock_func = mock_function(mock_SC_blobs=test_data)
    back_end = Backend('app', mock_func)

    test = back_end.upload_summary(summary_name)
    assert test == True 

def summary_model_fail(summary_name, summary_lst_data): 
    # Fails due to lengh of data being outside acceptable range  
    # i.e. lengh of data > max data length
    test_data = {summary_name : summary_lst_data}

    mock_func = mock_function(mock_SC_blobs=test_data, length=5) # length = max data length
    back_end = Backend('app', mock_func)
    test = back_end.upload_summary(summary_name)
    assert test == False

def summary_uploaded(summary_name, summary_lst_data):
    # Tests if summary produced from 'upload_summary'
    # properly uploads summary to GCS
    test_data = {summary_name : summary_lst_data}

    mock_func = mock_function(mock_SC_blobs=test_data)
    back_end = Backend('app', mock_func)
    
    test = back_end.upload_summary(summary_name)
    assert test == True
    actual = back_end.bucket_summary.blob(summary_name).download_as_text()
    assert 'hello there world' in actual

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


def test_comments_upload_sucess(comment_success):
    be = Backend('app', mock_function())
    success = be.upload_comment("sandy", comment_success.read())
    assert success == True


def test_comments_upload_fail(comment_failed):
    be = Backend('app', mock_function())
    success = be.upload_comment("sandy", comment_failed.read())
    assert success == False

def test_get_all_comments():
    be = Backend('app', mock_function())
    with patch.object(be.bucket_messages, 'list_blobs') as mock_list_blobs:
        mock_blob = blob_object("1680933371.7467146:sandy")
        mock_blob.upload_from_string("Hola Mundo")
        mock_blob2 = blob_object("1680936363.3217728:sandy")
        mock_blob2.upload_from_string("Hello")
        mock_list_blobs.return_value = [mock_blob, mock_blob2]
        comments_dict = be.get_comments()
        print(comments_dict)

    test_dict = {
        "user": "sandy",
        "time": "2023-04-08 05:56",
        "content": "Hola Mundo"
    }
    assert test_dict in comments_dict

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

def test_make_popularity_list():
    be = Backend(app, mock_function())
    with patch.object(be,
                      'make_popularity_list',
                       return_value=[
                          ['chord',3], ['dynamics',21], ['form',5], ['harmony',0], ['melody',2],
                          ['pitch',0], ['rhythm',0], ['scales',23], ['texture',12],
                          ['timbre',6]
                      ]):
        pages = be.make_popularity_list()
    assert type(pages[0]) == list


def test_get_history(valid_user):
    back_end = Backend('app', mock_function())
    back_end.sign_up(valid_user)
    back_end.sign_in(valid_user)
    history = back_end.get_history()
    assert len(history) == 4

def test_add_to_history(valid_user, page_name):
    back_end = Backend('app', mock_function())
    back_end.sign_up(valid_user)
    back_end.sign_in(valid_user)
    back_end.add_to_history(page_name)
    history = back_end.get_history()
    assert len(history) == 6
#test username:test password:test

### If using blob_test, follow format ###
        # blob_test = {<name_of_blob>.<extension> : test data,
        #              <name_of_blob>.<extension> : test data}

def test_make_popularity_list_other():
    test_info = {"Dictionary by Popularity.csv": 
                 'hello,4\n\rthere,3\n\rworld,1\n\r'}
    back_end = Backend('app', mock_function(mock_SC_blobs=test_info))
    
    make_actual = back_end.make_popularity_list()
    expected = [['hello',4], ['there',3], ['world',1]]
    
    assert expected == make_actual

def test_page_sort_by_pop():
    test_info = {"Dictionary by Popularity.csv": 
                 'hello,1\n\rthere,3\n\rworld,4\n\r'}
    back_end = Backend('app', mock_function(mock_SC_blobs=test_info))
    
    pop_actual = back_end.page_sort_by_popularity()
    expected = ['world', 'there', 'hello']
    assert expected == pop_actual

def test_sort_alpha():
    test_info = {'world.md':None, 'there.md':None, 'hello.md':None}
    back_end = Backend('app', mock_function(mock_SC_blobs=test_info))
    
    alpha_actual = back_end.get_all_page_names()
    expected = ['hello', 'there', 'world']
    
    assert expected == alpha_actual

def test_modify_page_analytics():
    test_info = {"Dictionary by Popularity.csv": 
                 'hello,1\n\rthere,3\n\rworld,2\n\r'}
    back_end = Backend('app', mock_function(mock_SC_blobs=test_info))
    
    modify_actual = back_end.modify_page_analytics()
    assert 'hello,1\r\nthere,3\r\nworld,2\r\n' == modify_actual

def test_pop_increment():
    test_info = {"Dictionary by Popularity.csv": 
                 'hello,1\n\rthere,3\n\rworld,2\n\r'}
    back_end = Backend('app', mock_function(mock_SC_blobs=test_info))
    back_end.get_wiki_page('hello')

    blob = back_end.bucket_page_stats.get_blob('Dictionary by Popularity.csv')
    incr_actual = blob.download_as_text()
    print(incr_actual)
    assert 'hello,2\r\nthere,3\r\nworld,2\r\n' == incr_actual


