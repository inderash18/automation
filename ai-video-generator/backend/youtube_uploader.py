import os
import sys
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Scopes required for video upload
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_service():
    """Authenticates the user and returns the YouTube API service object."""
    credentials = None
    
    # Locate token pickle from local cache
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.pickle")
    client_secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "client_secrets.json")
    
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            credentials = pickle.load(token)
            
    # Authenticate if credentials are not found or expired
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception:
                credentials = None
                
        if not credentials:
            if not os.path.exists(client_secrets_path):
                print(f"\n[YouTube Uploader Error]: 'client_secrets.json' was not found at {client_secrets_path}.", file=sys.stderr)
                print("To setup auto-uploading:\n"
                      "1. Go to Google Cloud Console (https://console.cloud.google.com)\n"
                      "2. Create a project, enable the YouTube Data API v3\n"
                      "3. Setup OAuth Consent Screen (Internal/External) and add test users\n"
                      "4. Download credentials (OAuth client ID -> Web/Desktop) as client_secrets.json and save it in the root folder.", file=sys.stderr)
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            credentials = flow.run_local_server(port=0)
            
        # Cache token for subsequent calls
        with open(token_path, "wb") as token:
            pickle.dump(credentials, token)
            
    return build("youtube", "v3", credentials=credentials)

def upload_video(video_path: str, title: str, description: str, tags: list, privacy_status: str = "private", progress_callback=None) -> str:
    """
    Uploads an MP4 file to the authenticated YouTube channel.
    Note: Google limits unverified applications to 'private' status uploads.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} does not exist.", file=sys.stderr)
        return ""
        
    youtube = get_youtube_service()
    if not youtube:
        return ""
        
    body = {
        "snippet": {
            "title": title[:100],  # Title character cap
            "description": description[:5000],  # Description cap
            "tags": tags[:50],  # Max tag limits
            "categoryId": "22"  # People & Blogs category
        },
        "status": {
            "privacyStatus": privacy_status,  # "private", "public", or "unlisted"
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    
    try:
        print(f"Starting YouTube upload stream: '{title}'...", flush=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                percent = int(status.progress() * 100)
                print(f"Upload progress: {percent}%", flush=True)
                if progress_callback:
                    try:
                        progress_callback(percent)
                    except Exception as cb_err:
                        print(f"Progress callback error: {cb_err}", file=sys.stderr)
                
        print(f"\nSuccessfully posted! Video ID: {response['id']}", flush=True)
        return response['id']
        
    except Exception as e:
        print(f"Failed to upload video: {str(e)}", file=sys.stderr)
        return ""

if __name__ == "__main__":
    # Test script run
    test_video = "output/final.mp4"
    if os.path.exists(test_video):
        print("Authenticating Google OAuth flow for testing...")
        upload_video(
            video_path=test_video,
            title="ShortsFlow Automated Test Upload",
            description="Generated autonomously by ShortsFlow Studio.",
            tags=["#shorts", "#automation", "#testing"],
            privacy_status="private"
        )
    else:
        print("Please compile a final.mp4 video file first before running upload tests.")
