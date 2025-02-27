import json
import os
import glob
import requests
import time
import base64
import lyricsgenius
from urllib.parse import quote

class GeniusLyricsFinder:
    def __init__(self, client_access_token):
        self.base_url = "https://api.genius.com"
        self.headers = {
            'Authorization': f'Bearer {client_access_token}'
        }
        
    def search_song(self, artist_name, track_name):
        """Search for a song on Genius"""
        search_url = f"{self.base_url}/search"
        search_term = f"{artist_name} {track_name}"
        params = {'q': search_term}
        
        try:
            response = requests.get(search_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'response' in data and 'hits' in data['response']:
                for hit in data['response']['hits']:
                    result = hit['result']
                    # Check if the artist name is in the result
                    if artist_name.lower() in result['primary_artist']['name'].lower():
                        return {
                            'title': result['title'],
                            'artist': result['primary_artist']['name'],
                            'lyrics_url': result['url'],
                            'song_id': result['id']
                        }
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error searching for lyrics: {e}")
            return None

def process_song_data(input_files, unique_songs_file, play_stats_file, lyrics_info_file, genius_token):
    # Dictionary to store unique songs (using track+artist as key)
    unique_songs = {}
    
    # Dictionary to store play counts and durations
    play_stats = {}
    total_plays = 0
    
    # Process each input file
    for file_path in input_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Process each song entry
                for entry in data:
                    # Create a unique key using artist and track name
                    key = f"{entry['artistName']}|{entry['trackName']}"
                    total_plays += 1
                    
                    # Store unique song if we haven't seen it before
                    if key not in unique_songs:
                        unique_songs[key] = {
                            "artistName": entry["artistName"],
                            "trackName": entry["trackName"]
                        }
                    
                    # Update play statistics
                    if key not in play_stats:
                        play_stats[key] = {
                            "artistName": entry["artistName"],
                            "trackName": entry["trackName"],
                            "playCount": 1,
                            "totalMsPlayed": entry.get("msPlayed", 0)
                        }
                    else:
                        play_stats[key]["playCount"] += 1
                        play_stats[key]["totalMsPlayed"] += entry.get("msPlayed", 0)
                        
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    # Convert dictionary values to list for JSON output
    unique_songs_list = list(unique_songs.values())
    play_stats_list = list(play_stats.values())
    
    # Add total song count to play stats
    play_stats_summary = {
        "totalUniqueSongs": len(unique_songs_list),
        "totalPlays": total_plays,
        "songStats": play_stats_list
    }
    
    # Write unique songs to output file
    with open(unique_songs_file, 'w', encoding='utf-8') as file:
        json.dump(unique_songs_list, file, indent=2, ensure_ascii=False)
    
    # Write play statistics to output file
    with open(play_stats_file, 'w', encoding='utf-8') as file:
        json.dump(play_stats_summary, file, indent=2, ensure_ascii=False)
    
    # Get lyrics info if token is provided
    if genius_token:
        lyrics_finder = GeniusLyricsFinder(genius_token)
        lyrics_info = []
        print(f"Looking up lyrics information for {len(unique_songs_list)} songs...")
        for i, song in enumerate(unique_songs_list):
            artist = song["artistName"]
            track = song["trackName"]
            
            # Add basic song info
            song_info = {
                "artistName": artist,
                "trackName": track
            }


            lyrics_info.append(song_info)
            search_track(token, track, artist)
            # Print progress
            if (i + 1) % 10 == 0 or i == len(unique_songs_list) - 1:
                print(f"Processed {i + 1}/{len(unique_songs_list)} songs")
                with open(lyrics_info_file, 'w', encoding='utf-8') as file:
                    json.dump(lyrics_info, file, indent=2, ensure_ascii=False)
            
            # Sleep to avoid rate limiting
            time.sleep(1)
        
        # Write lyrics info to output file
        with open(lyrics_info_file, 'w', encoding='utf-8') as file:
            json.dump(lyrics_info, file, indent=2, ensure_ascii=False)
        
        print(f"Lyrics information saved to {lyrics_info_file}")
    
    print(f"Found {len(unique_songs_list)} unique songs across all files.")
    print(f"Recorded {total_plays} total plays.")
    print(f"Unique songs saved to {unique_songs_file}")
    print(f"Play statistics saved to {play_stats_file}")
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
# Main execution
if __name__ == "__main__":
    # Get all JSON files in current directory
    input_files = glob.glob("*.json")
    
    # Remove the output files from input list if they exist
    unique_songs_file = "unique_songs.json"
    play_stats_file = "play_statistics.json"
    lyrics_info_file = "lyrics_info.json"
    
    output_files = [unique_songs_file, play_stats_file, lyrics_info_file]
    for output_file in output_files:
        if output_file in input_files:
            input_files.remove(output_file)
    
    # You need to register for a Genius API client access token
    # Get it from https://genius.com/api-clients
    genius_token = "XtxjNV501TUgVdb2f1LIjT4EiaAzjNRaey0iIcS0cVEFRYj5uud49RnleBHAe-1S"
    
    if not input_files:
        print("No JSON files found in current directory!")
    else:
        print(f"Processing {len(input_files)} JSON files...")
        process_song_data(input_files, unique_songs_file, play_stats_file, lyrics_info_file, genius_token)