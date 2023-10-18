import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

credentials = {}
with open("credentials.json") as json_file:
    credentials = json.load(json_file)
    
if(credentials != {}):
    start_time = time.time()

    scope = "user-library-read"
    spotify_client_id = credentials["spotify_client_id"]
    spotify_client_secret = credentials["spotify_client_secret"]

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=scope,
        client_id = spotify_client_id,
        client_secret = spotify_client_secret,
        redirect_uri = "http://localhost:3000"))

    # get all the users playlists
    playlists = []
    found_all = False
    offset = 0
    while(found_all == False):
        result = sp.current_user_playlists(limit=50, offset=offset)
        for idx, item in enumerate(result['items']):
            playlists.append({
                "name" : item["name"],
                "description": item["description"],
                "id": item["id"],
                "songs": []
            })
        offset += 50
        if(result["items"]==[]):
            found_all = True
    print(len(playlists), "playlists found!")

    # get all song titles and match them to the playlists
    for playlist in playlists:
        songs = []
        found_all = False
        offset = 0
        while(found_all == False):
            if(offset > 0):
                print("fetching playlist", playlist["name"], "...")
            result = sp.playlist_items(playlist["id"], limit = 100, offset = offset)["items"]
            for song in result:    
                title = song["track"]["name"]
                for artist in song["track"]["artists"]:
                    title += " " + artist["name"]
                songs.append(title)
            playlist["songs"] = songs
            offset += 100
            if(result == []):
                found_all = True
    
    # get favorites playlist
    found_all = False
    favs = []
    offset = 0
    # can get 50 songs max at once, so get multiple times
    while(found_all == False):
        results = sp.current_user_saved_tracks(offset = offset, limit = 50)
        for idx, item in enumerate(results['items']):
            title = item["track"]["name"]
            for artist in item["track"]["artists"]:
                title += " " + artist["name"]
            favs.append(title)
        offset += 50
        print("fetching favorites...")
        if(results['items'] == []):
            found_all = True

    if(favs != []):
        playlists.append({
            "name" : "your favorites from spotify",
            "description" : "this playlist contains all your liked songs from spotify",
            "id": "",
            "songs": favs
        })
    
    print("finished fetching all playlists!")
    total_songs=0
    for playlist in playlists:
        total_songs += len(playlist["songs"])
    print("fetched", len(playlists), "playlists containing a total of", total_songs, "songs in", time.time()-start_time, "s!")
  
else:
    print("error loading credentials")