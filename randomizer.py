from googleapiclient.discovery import build
from random import shuffle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import random

# Remove the API_KEY constant and add these instead
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CLIENT_SECRETS_FILE = "client_secrets.json"  # Path to your OAuth2 client configuration file

def get_credentials():
    print("Please authenticate in the browser window that will open...")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    print("Authentication successful!")
    return credentials

def get_short_videos():
    credentials = get_credentials()
    youtube = build('youtube', 'v3', credentials=credentials)
    
    video_ids = []
    next_page_token = None
    
    # Random search terms for variety
    search_terms = ['', 'a', 'e', 'i', 'o', 'u', 'the', 'be', 'to', 'of', 'and']
    
    while len(video_ids) < 200:
        print(f"Fetching more videos... Currently have {len(video_ids)}")
        
        search_request = youtube.search().list(
            part='id,snippet',
            maxResults=50,
            type='video',
            videoDuration='short',
            relevanceLanguage='en',
            eventType='none',
            q=random.choice(search_terms),  # Random basic search term
            pageToken=next_page_token
        )
        search_response = search_request.execute()
        
        next_page_token = search_response.get('nextPageToken')
        
        for search_result in search_response.get('items', []):
            if search_result['id']['kind'] == 'youtube#video':
                video_id = search_result['id']['videoId']
                
                # Get detailed video information
                video_request = youtube.videos().list(
                    part='contentDetails,snippet',
                    id=video_id
                )
                video_response = video_request.execute()
                video_info = video_response['items'][0]
                
                duration = video_info['contentDetails']['duration']
                minutes = duration.count('M')
                
                if (minutes == 0 or minutes <= 2) and \
                   not video_info['snippet'].get('liveBroadcastContent') == 'live':
                    video_ids.append(video_id)

                if len(video_ids) >= 200:
                    break
        
        if not next_page_token:
            # If we run out of results, try with a different random search
            next_page_token = None
            continue
    
    # Shuffle the final list for extra randomness
    shuffle(video_ids)
    print(f"Final video count: {len(video_ids)}")
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
                'description': 'A playlist of videos under 1 minute'
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
        print("Starting YouTube playlist creation...")
        
        # Delete existing playlist if it exists
        print("Checking for existing playlist...")
        delete_existing_playlist()
        
        # Get 50 short videos
        print("Fetching short videos...")
        video_ids = get_short_videos()
        
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