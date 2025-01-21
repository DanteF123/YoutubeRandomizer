from googleapiclient.discovery import build
from random import shuffle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import random
from datetime import datetime, timedelta

# Remove the API_KEY constant and add these instead
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CLIENT_SECRETS_FILE = "client_secrets.json"  # Path to your OAuth2 client configuration file

video_ids = set()

def get_random_datetime():
    start_date = datetime(2009, 1, 1)
    end_date = datetime.now()
    random_days = random.randint(0, (end_date - start_date).days)
    random_time = timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    random_date = start_date + timedelta(days=random_days) + random_time
    return random_date.strftime('%Y-%m-%dT%H:%M:%SZ')

def get_credentials():
    print("Please authenticate in the browser window that will open...")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    print("Authentication successful!")
    return credentials

def get_short_videos():
    global video_ids

    credentials = get_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)
    
    next_page_token = None

    # Generate random date between 2009 and now
    start_date = datetime(2009, 1, 1)  # YouTube launch date
    end_date = datetime.now()
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_days)

    while len(video_ids) < 50:
        try:
            search_request = youtube.search().list(
                part='id',
                maxResults=3,
                type='video',
                videoDuration='short',
                safeSearch='none',
                relevanceLanguage='en',
                eventType='none',
                order='date',
                publishedBefore=get_random_datetime(),
                pageToken=next_page_token
            )
            search_response = search_request.execute()
            
            # Get all video IDs from search
            batch_video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            # Get video details including category and channel info
            if batch_video_ids:
                video_request = youtube.videos().list(
                    part='snippet,status,contentDetails',
                    id=','.join(batch_video_ids)
                )
                video_response = video_request.execute()
                
                # Filter videos
                for video in video_response.get('items', []):
                    category_id = video['snippet']['categoryId']
                    # Exclude:
                    # - Music (10)
                    # - Shows (43)
                    # - Movies (30)
                    # - Trailers (44)
                    # - Entertainment (24) - often contains TV clips
                    if (category_id not in ['10', '43', '30', '44', '24'] and
                        video['snippet'].get('liveBroadcastContent', 'none') == 'none' and
                        not video.get('contentDetails', {}).get('licensedContent', False)):  # Exclude licensed content
                        
                        # Get channel details to verify it's not a verified/official channel
                        channel_request = youtube.channels().list(
                            part='status',
                            id=video['snippet']['channelId']
                        )
                        channel_response = channel_request.execute()
                        
                        # Check if channel is not verified/official
                        if channel_response.get('items'):
                            channel = channel_response['items'][0]
                            if not channel.get('status', {}).get('isLinked', False):  # Not a linked/official account
                                video_ids.add(video['id'])
            
            next_page_token = search_response.get('nextPageToken')
            if not next_page_token:
                break
                
        except Exception as e:
            print(f"Error fetching videos: {str(e)}")
            break
    
    # Shuffle the final list
    shuffle(video_ids)
    return video_ids

def create_playlist(video_ids):
    # Update the build call to use OAuth credentials
    credentials = get_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)
    
    # Create a new playlist
    playlists_insert_response = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': 'Short Videos Playlist',
                'description': 'A playlist of random short videos'
            },
            'status': {
                'privacyStatus': 'private'
            }
        }
    ).execute()
    
    playlist_id = playlists_insert_response['id']
    
    # Add videos to playlist
    for video_id in video_ids:
        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()
    
    return playlist_id

def delete_existing_playlist():
    credentials = get_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)
    
    # Get all playlists
    playlists = youtube.playlists().list(
        part='snippet',
        mine=True
    ).execute()
    
    # Find and delete the playlist with our specific title
    for playlist in playlists.get('items', []):
        if playlist['snippet']['title'] == 'Short Videos Playlist':
            youtube.playlists().delete(
                id=playlist['id']
            ).execute()
            print("Deleted existing playlist")
            break



def main():
    try:
        global video_ids
        print("Starting YouTube playlist creation...")
        
        # Delete existing playlist if it exists
        print("Checking for existing playlist...")
        delete_existing_playlist()
        
        # Get 50 short videos
        print("Fetching short videos...")
        while len(video_ids) < 50:
            get_short_videos()
        
        video_ids = list(video_ids)
        print(f"Found {len(video_ids)} videos")
        # Shuffle the videos for variety
        shuffle(video_ids)
        
        # Create playlist with these videos
        print("Creating new playlist...")
        playlist_id = create_playlist(video_ids)
        
        print(f"Playlist created successfully! ID: {playlist_id}")
        print(f"You can view it at: https://www.youtube.com/playlist?list={playlist_id}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()