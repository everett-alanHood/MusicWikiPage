from google.cloud import storage
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from datetime import datetime
#Hasing password
import bcrypt 
import base64
import hashlib
import os
import markdown

# for csv methods
import csv
from collections import deque

# Data processing
""" Pip install nltk, numpy, tensorflow """
from flaskr.stopwords import get_stopwords
import re
import numpy as np
import time
from datetime import datetime




# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing.text import tokenizer_from_json
from flaskr.mock_test import storage_client_mock, mock_model_load, mock_tokenizer_from_json


class Backend:
    """
    Wiki backend, which handles all operations for properly 
    running the site and connecting to GCS.

    Attributes:
        - bucket_{content,users,images,summary} (GCS Object): buckets from minorbugs GCS
        - all_pages    (set): All official wiki pages
        - max_data_len (int): Max length of input to generate summary
        - re_stop_word (Regex pattern object): Removes all stop words from a given string
        - re_link      (Regex pattern object): Removes all links from a given string
        - model        (Keras model): Keras model which is trained for text summarization
        - tokenize     (Keras tokenizer): Tokenizes data for model generation        
    Methods:
        - get_all_page_names:Gets all .md pages from GCS content
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

    def __init__(self, app, calls=(storage.Client(), mock_model_load, mock_tokenizer_from_json, 1600)):
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
        self.bucket_page_stats = storage_client.bucket('minorbugs_page_analytics')
        self.bucket_users.bucket_history = storage_client.bucket('user_history')        
        self.bucket_messages = storage_client.bucket('minorbugs_comments')
        
        #page urls
        pages = {
            '/', 'pages', 'about', 'welcome', 'login', 'logout', 'upload',
            'signup', 'images', 'history'
        }
        sub_pages = {
            'chord', 'harmony', 'pitch', 'rhythm', 'melody', 'scales', 'timbre',
            'form', 'dynamics', 'texture'
        }
        self.all_pages = pages | sub_pages
        self.current_username = ""
        
        # Pre-Processing for model input
        self.max_data_len = data_len
        stop_words = get_stopwords()
        self.re_stop_word = re.compile(f"\\b({'|'.join(stop_words)})\\b")
        self.re_link = re.compile(r'\[(.*?)\]\((.*?)\)')
        del stop_words
        
        # Load tokenizer
        blob = storage_client.bucket('minorbugs_model').blob('model_0/tokenizer.json')
        token_json = blob.download_as_string()
        self.tokenize = token_from_json(token_json)

        # Load model
        path = 'gs://minorbugs_model/model_0/'
        self.model = ml_load(f'{path}saved_model', compile=False)

    def get_history(self):
        """
        Gets the user's history from bucket_users
        Args: 
            N/A
        Returns:
            list of the user's pages and times
        """
        # Gets and cleans a users page history
        user_blob = self.bucket_users.blob(f'{self.current_username}')
        content = user_blob.download_as_string().decode('utf-8').split('\n')[2]
        content = content.replace('\'', '')
        content = content.strip('][\'').split(', ')

        if content[0] == "":
            return content[1:]
        return content
    
    def add_to_history(self, page_name):
        """
        Add the page name and time to the user's bucket \n
        Args: 
            name of a page (str)
        Returns:
            N/A
        """
        # Get users data
        user_blob = self.bucket_users.blob(f'{self.current_username}')
        content = user_blob.download_as_string().decode('utf-8').split('\n')
                
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')

        # Cleans log
        raw_log = content[2]
        raw_log = raw_log.replace('[', '')
        raw_log = raw_log.replace(']', '')
        raw_log = raw_log.replace('\'', '')
        raw_log = raw_log.split(', ')

        history = raw_log
        
        # Captures time and adds to users' history
        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history.append(page_name)
        history.append(timestamp)

        # Upload data
        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
    
    def get_all_page_names(self):
        """
        Gets all markdown sub-pages from google cloud buckets.\n
        Args: 
            - N/A
        Returns:
            - List of sub-page names (List)
        """
        # Gets all blobs from bucket_content
        all_blobs = list(self.bucket_content.list_blobs())

        #Set up for getting pages
        blocklist = ["test_model","TestMeet","test_url"]
        page_names = []

        # Adds applicable pages to page_names
        for blob in all_blobs:
            name = blob.name.split('.')
            if name[0] not in blocklist and name[-1] == 'md':
                page_names.append(name[0])
        
        # Sort and return page_names
        page_names.sort()
        return page_names
        
    def make_popularity_list(self):
        """
        Creates matrix of page names and 
        number times each page was visited.
        Args:
            - None
        Returns:
            - Matrix made of str and int 
        """
        # Get popularity stats
        blob = self.bucket_page_stats.get_blob("Dictionary by Popularity.csv")
        downloaded_file = blob.download_as_text(encoding="utf-8")
        page_data_list = list(downloaded_file)
        data = []
        string = ""

        # Creates string for each stat
        for index, character in enumerate(page_data_list):
            if (character == "," or character == "\r" or character == page_data_list[-1] ) and character != "\n":
                if character == page_data_list[-1]:
                    string = string + character
                data.append(string)
                string = ""
            elif character != "\n" and character != "\r":
                string = string+character
        
        temp = []
        true_data = []
        
        # Converts data popularity stat to int
        for index, pairs in enumerate(data):
            temp.append(pairs)            
            
            if index % 2 == 1:
                temp[1] = int(temp[1])
                true_data.append(temp.copy())
                temp.clear()
        
        return true_data
        
    def page_sort_by_popularity(self):
        """
        Gets the list of the pages and how often they've been looked at unorganized
        organizes them by popularity greatest to least \n
        Args: 
            N/A
        Returns:
            list of pages(str) without number ranking (list)
        """
        self.modify_page_analytics()
        p_list = self.make_popularity_list()

        # Sorts p_list data
        for next_pop in range(0, len(p_list)-1, 1):
            highest = p_list[next_pop][1]
            h_index = next_pop
            for find_highest in range(next_pop, len(p_list), 1):
                if p_list[find_highest][1] > highest:
                    highest = p_list[find_highest][1]
                    h_index = find_highest
            p_list[next_pop], p_list[h_index] = p_list[h_index], p_list[next_pop]
        
        # Gets name of page
        for page in range(len(p_list)):
            p_list[page] = p_list[page][0]
        
        return p_list
        
    def get_wiki_page(self, page_name):
        """
        Increments popularity value of sub page
        and converts a markdown file to HTML.\n       
        Args: 
            - Sub page name (Str)
        Returns:
            - HTML content (str)
        """
        bucket = self.bucket_page_stats
        blob = bucket.get_blob("Dictionary by Popularity.csv")        
        data = self.make_popularity_list()

        # Adds to sub-page popularity
        for index, pairs in enumerate(data):
            if pairs[0] == page_name:
                pairs[1] += 1

        # Converts data to string
        string = ""
        for index in data:
            string = string + index[0] + "," + str(index[1]) + "\r\n"
        
        # Uplods modified string 
        blob.upload_from_string(string)

        # Convert sub-page content to markdown
        md_blob = self.bucket_content.blob(f'{page_name}.md')
        md_content = md_blob.download_as_string().decode('utf-8')
        main = markdown.markdown(md_content)

        # Checks if summary for sub-page exists, if so, converts to markdown
        md_blob = self.bucket_summary.blob(f'{page_name}.md')
        if md_blob.exists():   
            md_content = md_blob.download_as_string().decode('utf-8')
            summary = markdown.markdown(md_content)
        else:
            summary = None

        return (main, summary)
    
    def modify_page_analytics(self):
        """
        Check if subpage analytics doesnt exist inside in the csv 
        and defult the ammount of times that the page was viewed to 0\n
        Args:
            - None
        Returns:
            - str (Only used in testing)
        """
        all_pages = self.get_all_page_names()
        bucket = self.bucket_page_stats
        blob = bucket.get_blob("Dictionary by Popularity.csv")
        csv_list = self.make_popularity_list()
        names = []
        string = ""
        
        # csv_list to string
        for x in csv_list:
            string = string + x[0] + "," + str(x[1]) + "\r\n"
            names.append(x[0])

        # Defaults new pages to 0 and adds to string
        for sub_page in all_pages:
            if sub_page not in names:
                names.append(sub_page)
                string = string + sub_page + "," + str(0) + "\r\n"
            
        blob.upload_from_string(string)
        return string

    def get_comments(self):
        """
        Gets all the comments stored in the Google Cloud buckets and returns
        them as a list of dictionaries containing all the comment info. \n
        Args:
            - N/A
        Returns: 
            - List of dictionaries representing the comments.
        """
        blobs = list(self.bucket_messages.list_blobs())
        comments_lst = []

        # Gets comments data from all users
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
        Receives a username and the comment content and formats the blob name as timestamp:username and then the contents of that blob
        is the message. It is then uploaded to the Google Cloud Buckets and then served with all the other comments. \n
        Args:
            - username: String representation of the logged in username.
            - content: String representation of the comment typed out by the user in the comment text input.
        Returns: 
            - Boolean representing if the upload was successful or not.
        """
        if not content:
            return False

        # Gets current time
        timestamp = str(time.time())
        filename = timestamp + ":" + username
        message_blob = self.bucket_messages.blob(filename)

        if message_blob.exists():
            return False

        # Uploads content to bucket
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
            # Checks for any invalid links
            if not self.url_check(content, filename):
                return False
            content.seek(0)
            blob = self.bucket_content.blob(os.path.basename(filename))
        elif file_end in {"jpeg", "jpg", "png"}:
            blob = self.bucket_images.blob(os.path.basename(filename))
        else:
            return False

        # Uploads data to cloud
        blob.upload_from_file(content)

        # If md file, upload summary
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
        Checks if a .md file has valid links to the site\n
        Args: 
            - Contents of a file (IO), the filename (Str)
        Returns: 
            - (Boolean)
        """
        content = str(file_content.read())
        check_urls = re.findall(r'\[(.*?)\]\((.*?)\)', content)
        
        # Checks for invalid links in md file
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
        blobs = list(self.bucket_images.list_blobs())
        images_lst = []

        # Adds all images to images_lst (Except authors)
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
        blobs = list(self.bucket_images.list_blobs())
        images_lst = []

        # Gets all author images from GCS images
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

        # Checks if user exists
        if user_blob.exists():
            return False, ''

        # Gets name & password
        user_pass = user_info['password']
        name = user_info['name']

        # Gets timestap for new account
        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history = ["Account Began", timestamp]
        
        # Encrypts password
        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())
        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(encoded, salt)

        # Uploads users data
        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
        self.current_username = user_name

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

        # Check if user doesnt exist
        if not user_blob.exists():
            return False, ''

        # Gets users data (username & password)
        content = user_blob.download_as_string().decode('utf-8').split('\n')
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')
        
        if len(content) == 2:
            content.append("")

        # Cleans log content
        raw_log = content[2]
        raw_log = raw_log.replace('[', '')
        raw_log = raw_log.replace(']', '')
        raw_log = raw_log.replace('\'', '')
        raw_log = raw_log.split(', ')

        history = raw_log
        
        # Captures current time
        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history.append("Logged In")
        history.append(timestamp)

        # Encrypts pass just passed in
        user_pass = user_check['password']
        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())

        # Checks if encrypted password matches one on records
        if not bcrypt.checkpw(encoded, hash_pass):
            return False, ''

        # Uploads users data
        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
        self.current_username = user_name

        return True, name

    def get_log(self):
        pass