from randomizer import get_credentials,SCOPES,CLIENT_SECRETS_FILE
from googleapiclient.discovery import build
from random import shuffle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import random

def get_URL():
    credentials = get_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)

    search_request = youtube.search().list(
        part='id,snippet',
        maxResults=1,
        type='video',
        videoDuration='short',
        relevanceLanguage='en',
        eventType='none',
        id = 'isWBy5I4TnQ'
    )
    search_response = search_request.execute()

    for search_result in search_response.get('items',[]):
        print(search_result)


get_URL()