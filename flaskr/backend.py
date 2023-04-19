from google.cloud import storage
from flask import Flask, render_template, redirect, request, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from datetime import datetime
#Hasing password
import bcrypt  #gensalt, hashpw, checkpw
import base64
import hashlib
import os
# from markdown import markdown
import markdown
import re
# for csv methods
import csv
from collections import deque

import time
from datetime import datetime
"""
Explanation
Args:
Returns:
"""


class Backend:
    """
    Explain

    Attributes:
        bucket_content: 
        bucket_users: 
        bucket_images: 
        pages: Set of all pages on necessary pages on wiki
        sub_pages: Set of all sub-pages to pages.html
        all_pages: All valid pages on the wiki (Union of pages and sub_pages)
    """

    def __init__(self, app, SC=storage.Client()):
        """
        Args: 
            An App from flask (ex. Flask(__name__) )
        Explain: 
            Initializes and creates necessary attributes for backend
        """
        test_app = Flask(__name__)
        self.login_manager = LoginManager()
        self.login_manager.init_app(test_app)
        #Buckets
        storage_client = SC
        self.bucket_content = storage_client.bucket('minorbugs_content')
        self.bucket_users = storage_client.bucket('minorbugs_users')
        self.bucket_images = storage_client.bucket('minorbugs_images')
        self.bucket_page_stats = storage_client.bucket('minorbugs_page_analytics')
        self.bucket_users.bucket_history = storage_client.bucket('user_history')        
        self.bucket_messages = storage_client.bucket('minorbugs_comments')
        #page urls
        self.pages = {
            '/', 'pages', 'about', 'welcome', 'login', 'logout', 'upload',
            'signup', 'images', 'history'
        }
        self.sub_pages = {
            'chord', 'harmony', 'pitch', 'rhythm', 'melody', 'scales', 'timbre',
            'form', 'dynamics', 'texture'
        }
        self.all_pages = self.pages | self.sub_pages
        self.current_username = ""

    def get_history(self):
        """
        Args: 
            Nothing
        Explain:
            gets the user's history from bucket_users
        Returns:
            list of the user's pages and times
        """
        user_blob = self.bucket_users.blob(f'{self.current_username}')
        content = user_blob.download_as_string().decode('utf-8').split('\n')[2]
        content = content.replace('\'', '')
        content = content.strip('][\'').split(', ')
        if content[0] == "":
            return content[1:]
        return content
    
    def add_to_history(self, page_name):
        """
        Args: 
            name of a page (str)
        Explain:
            add the page name and time to the user's bucket
        Returns:
            nothing
        """
        user_blob = self.bucket_users.blob(f'{self.current_username}')
        content = user_blob.download_as_string().decode('utf-8').split('\n')
        
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')

        raw_log = content[2]
        raw_log = raw_log.replace('[', '')
        raw_log = raw_log.replace(']', '')
        raw_log = raw_log.replace('\'', '')
        raw_log = raw_log.split(', ')

        history = raw_log
        
        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history.append(page_name)
        history.append(timestamp)

        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
    
    def get_all_page_names(self):
        """
        Args: 
            Nothing
        Explain:
            Gets all markdown sub-pages from google cloud buckets
        Returns:
            List of sub-page names (List)
        """
        all_blobs = list(self.bucket_content.list_blobs())
        #Could add a feature where users upload their own content??
        
        page_names = []
        blocklist=["test_model","TestMeet","test_url"]
        for blob in all_blobs:
            name = blob.name.split('.')
            if name[0] not in blocklist and name[-1] == 'md':
                page_names.append(name[0])
                
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
        bucket = self.bucket_page_stats
        blob = bucket.get_blob("Dictionary by Popularity.csv")
        downloaded_file = blob.download_as_text(encoding="utf-8")
        page_data_list = list(downloaded_file)
        data = []
        string = ""
        for index ,character in enumerate(page_data_list):
            if (character == "," or character == "\r" or character == page_data_list[-1] ) and character != "\n":
                print(str(page_data_list[-1]))
                if character == page_data_list[-1]:
                    string = string + character
                data.append(string)
                string = ""
            elif character != "\n" and character != "\r":
                string = string+character
        temp = []
        true_data = []
        
        for index , pairs in enumerate (data):
            temp.append(pairs)            
            
            if index%2 == 1:
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
        p_list=self.make_popularity_list()


        
        for next_pop in range(0, len(p_list)-1, 1):
            highest = p_list[next_pop][1]
            h_index = next_pop
            for find_highest in range(next_pop, len(p_list), 1):
                if p_list[find_highest][1] > highest:
                    highest = p_list[find_highest][1]
                    h_index = find_highest
            p_list[next_pop], p_list[h_index] = p_list[h_index], p_list[next_pop]
        
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
        ### Transfered from pages.py ###
        bucket = self.bucket_page_stats
        blob = bucket.get_blob("Dictionary by Popularity.csv")        
        data = self.make_popularity_list()
        string = ""

        for index, pairs in enumerate(data):
            if pairs[0] == page_name:
                pairs[1] += 1

        string = ""
        for index in data:
            string = string + index[0] + "," + str(index[1]) + "\r\n"
        
        blob.upload_from_string(string)

        md_blob = self.bucket_content.blob(f'{page_name}.md')
        md_content = md_blob.download_as_string().decode('utf-8')
        html_content = markdown.markdown(md_content)

        return html_content
    
    def modify_page_analytics(self):
        """This check if a subpage analytics doesnt exist inside in the csv 
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
        for x in csv_list:
            string = string+x[0] + "," + str(x[1]) + "\r\n"
            names.append(x[0])

        for sub_page in all_pages:
            if sub_page not in names:
                names.append(sub_page)
                string = string + sub_page + "," + str(0) + "\r\n"
            
        blob.upload_from_string(string)
            
        csv_files = list(self.bucket_page_stats.list_blobs())
        return string

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
        Args: Nothing
        Explain: Retrieves image urls from google cloud 
                 buckets (Content and Images), excluding authors.
        Returns: List of image urls (List)
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
        Args: Nothing
        Explain: Retrieves image urls from google cloud 
                 buckets (Images), only authors.
        Returns: List of image urls and author names (List)
        """
        storage_client = storage.Client()
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
        Args: A users info (Dict(name, username, password))
        Explain: Adds user to GCB (users), if they dont 
                 already exist and allows login.
        Returns: (Boolean), A user's name or empty (str)
        """
        user_name = user_info['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')

        if user_blob.exists():
            return False, ''

        user_pass = user_info['password']
        name = user_info['name']

        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history = ["Account Began", timestamp]


        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())
        salt = bcrypt.gensalt()
        hash_pass = bcrypt.hashpw(encoded, salt)

        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
        self.current_username = user_name
        return True, name

    def sign_in(self, user_check):
        """
        Args: Users sign-in info ( Dict(username, password) )
        Explain: Checks if an existing user entered the correct 
                 credentials and allows for login.
        Returns: (Boolean), A user's name or empty (str)
        """
        user_name = user_check['username'].lower()
        user_blob = self.bucket_users.blob(f'{user_name}')

        if not user_blob.exists():
            return False, ''

        content = user_blob.download_as_string().decode('utf-8').split('\n')
        name = content[0]
        hash_pass = content[1][2:-1].encode('utf-8')
        
        if len(content) == 2:
            content.append("")

        raw_log = content[2]
        raw_log = raw_log.replace('[', '')
        raw_log = raw_log.replace(']', '')
        raw_log = raw_log.replace('\'', '')
        raw_log = raw_log.split(', ')

        history = raw_log
        
        now = datetime.now()
        timestamp = now.strftime("%b-%d-%Y %H:%M:%S")
        history.append("Logged In")
        history.append(timestamp)

        user_pass = user_check['password']
        mixed = f'{user_pass}hi{user_name}'
        encoded = base64.b64encode(hashlib.sha256(mixed.encode()).digest())

        if not bcrypt.checkpw(encoded, hash_pass):
            return False, ''

        user_blob.upload_from_string(f"{name}\n{hash_pass}\n{history}")
        self.current_username = user_name

        return True, name

    def get_log(self):
        pass