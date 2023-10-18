import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

credentials = {}
with open("credentials.json") as json_file:
    credentials = json.load(json_file)
    
if(credentials != {}):
    scope = "user-library-read"
    spotify_client_id = credentials["spotify_client_id"]
    spotify_client_secret = credentials["spotify_client_secret"]

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=scope,
        client_id = spotify_client_id,
        client_secret = spotify_client_secret))

    results = sp.current_user_saved_tracks()
    for idx, item in enumerate(results['items']):
        track = item['track']
        print(idx, track['artists'][0]['name'], " - ", track['name'])
else:
    print("error loading credentials")