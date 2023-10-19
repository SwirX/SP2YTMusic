import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
import ytmusicapi
from ytmusicapi import YTMusic

credentials = {}
with open("credentials.json") as json_file:
    credentials = json.load(json_file)

ytmusic = 0

if(not os.path.isfile("oauth.json")):
    print("generating youtube api tokens")
    oauth = ytmusicapi.setup_oauth(open_browser = True)
    with open("oauth.json", "w") as json_file:
        json_file.write(json.dumps(oauth, indent=4))

ytmusic = YTMusic("oauth.json")

if(credentials != {} or ytmusic == 0):
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
            "id": "favs",
            "songs": favs
        })
    
    print("finished fetching all playlists!")
    total_songs=0
    for playlist in playlists:
        total_songs += len(playlist["songs"])
    print("fetched", len(playlists), "playlists containing a total of", total_songs, "songs in", time.time()-start_time, "s!")
  
    # create new playlists in youtube music
    yt_playlists = []
    print("Looking for all your spotify songs on youtube, this may take a while..")
    start_time = time.time()
    # replace all query strings with corresponding yt music ids
    for playlist in playlists:
        song_ids = []
        progress = 0
        print("fetching yt music ids for songs in", playlist["name"])
        for song_title in playlist["songs"]:
            song_id = ytmusic.search(song_title, limit = 1, filter = "songs")[0]["videoId"]
            song_ids.append(song_id)
            progress += 1
            if(progress % 10 == 0):
                print(progress, "/", len(playlist["songs"]))
        yt_playlists.append(playlist)
        yt_playlists[-1]["songs"] = song_ids
    print("Fetched songs ids from all songs in", time.time()-start_time, "s!")
    print("Creating all playlists in yt music.")

    for playlist in yt_playlists:
        ytmusic.create_playlist(
            playlist["name"],
            playlist["description"],
            video_ids = playlist["songs"]
        )
        print("Created playlist", playlist["name"])
        if(playlist["id"]=="favs"):
            print("Do you want me to like all the songs in your 'favorite songs' playlist, so that they appear in youtube's automatically generated playlist?")
            input = input("enter 'y' for yes, anything else for no")
            if(input in ["y", "Y", "yes", "Yes"]):
                for song in playlist["songs"]:
                    ytmusic.rate_song(song, "LIKE")

else:
    print("error loading credentials")