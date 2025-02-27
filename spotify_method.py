import json,os,requests

def load_unique_songs():
    unique_songs_file = "unique_songs.json"

    with open(unique_songs_file, 'r', encoding='utf-8') as file:
        unique_songs_list = json.load(file)

    print(f"Looking up lyrics information for {len(unique_songs_list)} songs...")

    for i, song in enumerate(unique_songs_list):
        artist = song["artistName"]
        track = song["trackName"]
        
        # Add basic song info
        song_info = {
            "artistName": artist,
            "trackName": track
        }

# Function to search for a track
def getToken():
    try:
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        response = requests.post(
            f'https://accounts.spotify.com/api/token',
            headers=headers,
            data=data
        )

        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        return data['access_token']
       
    except Exception as error:
        print(f'Error  : {str(error)}')
        return None

# Function to search for a track
async def search_track(token, track_name, artist_name):
    try:
        query = f"track:{track_name} artist:{artist_name}"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = requests.get(
            f'https://api.spotify.com/v1/search?q={requests.utils.quote(query)}&type=track&limit=1',
            headers=headers
        )
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        if data['tracks']['items']:
            return data['tracks']['items'][0]['id']
        else:
            print(f"No track found for: {track_name} by {artist_name}")
            return None
    except Exception as error:
        print(f'Error searching for track "{track_name}": {str(error)}')
        return None
    
token =  getToken()
print(token)