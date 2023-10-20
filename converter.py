import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
import ytmusicapi
from ytmusicapi import YTMusic

total_time = time.time()
print("Getting spotify credentials...")
credentials = {}
with open("credentials.json") as json_file:
    credentials = json.load(json_file)

print("Getting yt music credentials...")
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
    print("Finding all playlists on spotify...")
    playlists = []
    if(not os.path.isfile("spotify_playlists.json")):
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
        print("Getting all song titles...")
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
        
        print("Finished fetching all playlists!")
        total_songs=0
        for playlist in playlists:
            total_songs += len(playlist["songs"])
        print("Fetched", len(playlists), "playlists containing a total of", total_songs, "songs in", time.time()-start_time, "s.")
        with open("spotify_playlists.json", "w") as json_file:
                json_file.write(json.dumps(playlists, indent=4))
    else:
        with open("spotify_playlists.json") as json_file:
            playlists = json.load(json_file)
            print("Loaded spotify playlists from file.")

    # create new playlists in youtube music
    yt_playlists = []
    not_found_songs = []
    found_songs = {}

    if(not os.path.isfile("yt_playlists.json")):
        skipped = 0
        print("Looking for all your spotify songs on youtube, this may take a while..")
        start_time = time.time()
        # replace all query strings with corresponding yt music ids
        for playlist in playlists:
            song_ids = []
            not_found = []
            progress = 0
            print("Fetching yt music ids for songs in", playlist["name"])
            for song_title in playlist["songs"]:
                song_id = None
                if(song_title in found_songs.keys()):
                    song_id = found_songs[song_title]
                    skipped += 1
                else:
                    result = next(iter(ytmusic.search(song_title, limit = 1, filter = "songs")), None)
                    if(result is not None):
                        song_id = result["videoId"]
                        found_songs[song_title] = song_id
                    else:
                        print("Song", song_title,"could not be found. All songs which weren't added are getting shown again at the end.")
                        not_found.append(song_title)
                
                if(song_id is not None):
                    song_ids.append(song_id)
                progress += 1
                if(progress % 10 == 0):
                    print(progress, "/", len(playlist["songs"]))

            yt_playlists.append(playlist)
            yt_playlists[-1]["songs"] = song_ids
            if(not_found != []):
                not_found_songs.append({playlist["name"]:not_found})

        print("skipped", skipped, "queries")
        print("Fetched songs ids from all songs in", time.time()-start_time, "s!")
        print("Creating all playlists in yt music.")


        with open("yt_playlists.json", "w") as json_file:
            json_file.write(json.dumps(yt_playlists, indent=4))
    else:
        with open("yt_playlists.json") as json_file:
            yt_playlists = json.load(json_file)
            print("Loaded yt music playlists from file.")

    for playlist in yt_playlists:
        ytmusic.create_playlist(
            playlist["name"].replace("<", "(").replace(">", ")"),     # for whatever reason these symbols arent allowed in playlist names
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

    if(not_found_songs != []):
        print("Couldnt find the following song:")
        for playlist_name, songs in not_found_songs:
            print(playlist_name)
            for song in songs:
                print("-", song)

    print("Finished in", total_time - time.time(), "s.")

else:
    print("error loading credentials")