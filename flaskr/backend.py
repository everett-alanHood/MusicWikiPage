from google.cloud import storage
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
#Hasing password
import bcrypt  #gensalt, hashpw, checkpw
import base64
import hashlib
import os
import markdown

# Data processing
""" Pip install nltk, numpy, tensorflow """
import re
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import tokenizer_from_json
import time
from datetime import datetime

"""
Explanation
Args:
Returns:
"""


class Backend:
    """
    Wiki backend, which handles all operations for properly 
    running the site and connecting to GCS.

    Attributes:
        - bucket_{content,users,images,summary} (GCS Object): buckets from minorbugs GCS
        - all_pages    (set): ...
        - max_data_len (int): Max length of input to generate summary
        - re_stop_word (Regex pattern object): Removes all stop words from a given string
        - re_link      (Regex pattern object): Removes all links from a given string
        - model        (Keras model): Keras model which is trained for text summarization
        - tokenize     (Keras tokenizer): Tokenizes data for model generation        
    Methods:
        - get_all_page_names: ...
        - get_wiki_page:     Gets content from an uploaded sub-page
        - upload:            Uploads a file to GCS
        - remove_stop_words: Calls re_stop_word to remove all stop words before generating a summary
        - re_link:           Calls re_link to remove all links before generating a summary
        - upload_summary:    Uploads an md file summary to GCS
        - url_check:         Checks if all links in an md file are valid
        - get_image:         Retrieve all images from GCS
        - sign_up:           Signs a user up for a wiki account, asssuming they dont have one
        - sign_in:           Signs in a user their account
    """

    def __init__(self, app, calls=(storage.Client(), load_model, tokenizer_from_json, 1600)):
        """
        Initializes and creates necessary attributes for backend.\n
        Args: 
            - App from flask (ex. Flask(__name__) )      
            - length 4 vector (Optional)
                - (GCS client, keras load_model instance, keras tokenizer from json instance, max data length)      
        """
        SC, ml_load, token_from_json, data_len = calls

        test_app = Flask(__name__)
        self.login_manager = LoginManager()
        self.login_manager.init_app(test_app)
        #Buckets
        storage_client = SC
        self.bucket_content = storage_client.bucket('minorbugs_content')
        self.bucket_users = storage_client.bucket('minorbugs_users')
        self.bucket_images = storage_client.bucket('minorbugs_images')
        self.bucket_summary = storage_client.bucket('minorbugs_summary')
        self.bucket_messages = storage_client.bucket('minorbugs_comments')
        
        #page urls
        pages = {
            '/', 'pages', 'about', 'welcome', 'login', 'logout', 'upload',
            'signup', 'images'
        }
        sub_pages = {
            'chord', 'harmony', 'pitch', 'rhythm', 'melody', 'scales', 'timbre',
            'form', 'dynamics', 'texture'
        }
        self.all_pages = pages | sub_pages

        # Pre-Processing for model input
        self.max_data_len = data_len
        stop_words = stopwords.words('english')
        self.re_stop_word = re.compile(f"\\b({'|'.join(stop_words)})\\b")
        self.re_link = re.compile(r'\[(.*?)\]\((.*?)\)')
        del stop_words

        # Load model
        path = 'gs://minorbugs_model/model_0'
        self.model = ml_load(f'{path}saved_model')
        
        # Load tokenizer
        blob = storage_client.bucket('minorbugs_model').blob('model_0/tokenizer.json')
        token_json = blob.download_as_string()
        self.tokenize = token_from_json(token_json)

    def get_all_page_names(self):
        """
        Gets all markdown sub-pages from google cloud buckets.\n
        Args: 
            - N/A
        Returns:
            - List of sub-page names (List)
        """
        all_blobs = list(self.bucket_content.list_blobs())

        page_names = []
        for blob in all_blobs:
            name = blob.name.split('.')
            if name[-1] == 'md':
                page_names.append(name[0])

        page_names.sort()
        return page_names

    def get_wiki_page(self, page_name):
        """
        Converts a specific markdown file to html, 
        adds the header, and stores that in local files.\n
        Args: 
            - A page name (Str)
        Returns: 
            - N/A
        """
        md_blob = self.bucket_content.blob(f'{page_name}.md')
        md_content = md_blob.download_as_string().decode('utf-8')
        html_content = markdown.markdown(md_content)

        return html_content

    def get_comments(self):
        """
        Args: self
        Explain: Gets all the comments stored in the Google Cloud buckets and returns
        them as a list of dictionaries containing all the comment info.
        Returns: List of dictionaries representing the comments.
        """
        blobs = list(self.bucket_messages.list_blobs())
        comments_lst = []
        for blob in blobs:
            metadata = blob.name.split(":")
            timestamp = str(datetime.fromtimestamp(float(metadata[0])))[0:-10]
            user = metadata[1]
            comments_dict = {
                "user": user,
                "time": timestamp,
                "content": blob.download_as_string().decode('utf-8')
            }
            comments_lst.append(comments_dict)
        return comments_lst

    def upload_comment(self, username, content):
        """
        Args:
        username: String representation of the logged in username.
        content: String representation of the comment typed out by the user in the comment text input.
        Explain: Receives a username and the comment content and formats the blob name as timestamp:username and then the contents of that blob
        is the message. It is then uploaded to the Google Cloud Buckets and then served with all the other comments.
        Returns: 
        Boolean representing if the upload was successful or not.
        """
        if not content:
            return False
        timestamp = str(time.time())
        filename = timestamp + ":" + username
        message_blob = self.bucket_messages.blob(filename)
        if message_blob.exists():
            return False
        message_blob.upload_from_string(content)
        return True

    def upload(self, content, filename):
        """
        Uploads a .md, .jpg, .jpeg or .png,
        to a google cloud bucket (Content or Images)\n
        Args: 
            - Contents of a file (IO), the filename (Str)
        Returns: 
            - (Boolean)
        """
        file_end = filename.split(".")[-1].lower()

        if file_end == "md":
            if not self.url_check(content, filename):
                return False
            content.seek(0)
            blob = self.bucket_content.blob(os.path.basename(filename))
        
        elif file_end == "jpeg" or file_end == "jpg" or file_end == "png":
            blob = self.bucket_images.blob(os.path.basename(filename))
        
        else:
            return False

        blob.upload_from_file(content)
        if file_end == "md":
            self.upload_summary(filename)
        
        return True
        
    def remove_stop_words(self, text):
        """
        Removes stop words from text.\n
        Args:
            - Original text (str)
        Returns:
            - Cleaned text (str)
        """        
        return self.re_stop_word.sub('', text)

    def remove_links(self, text):
        """
        Removes links from text.\n
        Args:
            - Original text (str)
        Returns:
            - Cleaned text (str)
        """        
        return self.re_link.sub('', text)

    def upload_summary(self, filename):
        """
        Pre-Processes and cleans file text, generates
        summary from model and uploads the summary
        to the minorbugs_summary bucket.\n
        Args:
            - filename (Str), name of .md file
        Returns:
            - (Boolean)
        """
        md_blob = self.bucket_content.blob(filename)
        md_lines = md_blob.open('rb') #blob.read().decode("utf-8")
        no_header_str = ''
        
        # Removes header and converts bytes to strings
        for line in md_lines:
            line = line.decode('utf-8')
            if len(line) < 1 or line[0] == '#': 
                continue
            no_header_str += line + ' '
        
        # Removes links and unnecessary words from string
        no_stop_words = self.remove_stop_words(no_header_str.lower())
        cleaned_str = self.remove_links(no_stop_words)

        # Limits the data to avoid excessive computational time
        if len(cleaned_str) > self.max_data_len: 
            return False

        # Converts string to data that model can understand
        token_data_encode = np.array([self.tokenize.texts_to_sequences([cleaned_str])])[0]
        data_decode = np.zeros([1, token_data_encode.shape[1]])
        data_decode[0] = self.tokenize.word_index['<sos>']
        
        # Generates summary and converts back to readable data 
        token_summary = self.model.predict([token_data_encode, data_decode])
        max_preds = np.argmax(token_summary, axis=-1)
        list_summary = self.tokenize.sequences_to_texts(max_preds)
        str_summary = ' '.join(list_summary)    
  
        # Uploads summary to cloud
        blob = self.bucket_summary.blob(filename)
        blob.upload_from_string(str_summary)
        
        return True

    def url_check(self, file_content, filename):
        """
        Checks if an md file has valid links to the site\n
        Args: 
            - Contents of a file (IO), the filename (Str)
        Returns: 
            - (Boolean)
        """
        content = str(file_content.read())
        check_urls = re.findall(r'\[(.*?)\]\((.*?)\)', content)

        for url in check_urls:
            if url[1][1:] in self.all_pages:
                pass
            elif url[1][2:] in self.all_pages:
                pass
            else:
                return False
        return True

    def get_image(self):
        """
        Retrieves image urls from google cloud 
        buckets (Content and Images), excluding authors.\n
        Args: 
            - N/A
        Returns: 
            - List of image urls (List)
        """
        #storage_client = storage.Client()
        #bucket = self.bucket_content
        blobs = list(self.bucket_content.list_blobs())
        blobs = list(self.bucket_images.list_blobs())
        images_lst = []

        for blob in blobs:
            if blob.name.startswith("[Author]"):
                continue
            blob_img = blob.public_url
            images_lst.append(blob_img)

        images_lst.sort()
        return images_lst

    def get_about(self):
        """
        Retrieves image urls from google cloud 
        buckets (Images), only authors.\n
        Args: 
            - Nothing
        Returns: 
            - List of image urls and author names (List)
        """
        # storage_client = storage.Client()
        blobs = list(self.bucket_images.list_blobs())
        images_lst = []
        for blob in blobs:
            if blob.name.startswith("[Author]"):
                blob_img = blob.public_url
                name = blob.name.split(",")[1]
                images_lst.append((blob_img, name))
            else:
                continue

        images_lst.sort()
        return images_lst

    def sign_up(self, user_info):
        """
        Adds user to GCB (users), if they dont 
        already exist and allows login.\n
        Args: 
            - A users info, Dict(name, username, password)
        Returns: 
            - (Boolean), A user's name or empty (str)
        """
        user_name = user_info['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')

        if user_blob.exists():
            return False, ''

        user_pass = user_info['password']
        name = user_info['name']

        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())
        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(encoded, salt)

        user_blob.upload_from_string(f"{name}\n{hash_pass}")
        return True, name

    def sign_in(self, user_check):
        """
        Checks if an existing user entered the correct 
        credentials and allows for login.\n
        Args: 
            - Users sign-in info ( Dict(username, password) )
        Returns: 
            - (Boolean), A user's name or empty (str)
        """
        user_name = user_check['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')

        if not user_blob.exists():
            return False, ''

        content = user_blob.download_as_string().decode('utf-8').split('\n')
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')

        user_pass = user_check['password']
        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())

        if not bcrypt.checkpw(encoded, hash_pass):
            return False, ''

        return True, name
