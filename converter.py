import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
import ytmusicapi
from ytmusicapi import YTMusic

def get_all_spotify_songs_from_query_result(items):
    output = []
    for song in items:    
        title = song["track"]["name"]
        for artist in song["track"]["artists"]:
            title += " " + artist["name"]
        if(title.replace(" ", "") != ""): # filter deleted songs
            output.append(title)
    return output

def find_all_spotify_songs_in_playlist(playlist_id):
    songs = []
    found_all = False
    offset = 0
    while(found_all == False):
        result = sp.playlist_items(playlist_id, limit = 100, offset = offset)["items"]
        if(result == []):
            found_all = True
        else:
            songs.extend(get_all_spotify_songs_from_query_result(result))
            offset += 100
    return songs

def find_favorite_spotify_songs(sp):
    found_all = False
    favs = []
    offset = 0
    print("fetching favorites...")
    while(found_all == False):
        result = sp.current_user_saved_tracks(offset = offset, limit = 50)['items']
        favs.extend(get_all_spotify_songs_from_query_result(result))
        offset += 50
        if(result == []): 
            found_all = True

    if(favs != []):
        return {
            "name" : "your favorites from spotify",
            "description" : "this playlist contains all your liked songs from spotify",
            "songs": favs
        }
    return []

def find_all_spotify_playlists(sp):
    found_all = False
    offset = 0
    spotify_playlists = []
    while(found_all == False):
        result = sp.current_user_playlists(limit=50, offset=offset)
        for item in result['items']:
            print("fetching playlist", item["name"], "...")
            songs = find_all_spotify_songs_in_playlist(item["id"])
            spotify_playlists.append({
                "name" : item["name"],
                "description": item["description"],
                "songs": songs
            })
        offset += 50
        if(result["items"]==[]):
            found_all = True
    spotify_playlists.append(find_favorite_spotify_songs(sp))
    print(len(spotify_playlists), "playlists found!")
    return spotify_playlists

def get_all_ytm_ids(spotify_playlists):
    output = []
    not_found_songs = []
    found_songs = {}
    print("Looking for all your spotify songs on youtube, this may take a while..")
    start_time = time.time()
    # replace all query strings with corresponding yt music ids
    for playlist in spotify_playlists:
        song_ids = []
        not_found = []
        progress = -1

        print("Fetching yt music ids for songs in", playlist["name"])
        for song_title in playlist["songs"]:
            progress += 1
            if(progress % 10 == 0):
                print(progress, "/", len(playlist["songs"]))

            # skip query if song has been searched before
            if(song_title in found_songs.keys()):
                song_ids.append(found_songs[song_title])
                progress
                continue
            
            # search for song title on yt music
            result = next(iter(ytmusic.search(song_title, limit = 1, filter = "songs")), None)
            if(result is not None):
                song_id = result["videoId"]
                found_songs[song_title] = song_id
                song_ids.append(song_id)
            else:
                print("Song", song_title, "could not be found. All songs which weren't added are getting shown again at the end.")
                not_found.append(song_title)

        if(not_found != []):
            not_found_songs.append({playlist["name"]:not_found})
        output.append(playlist)
        output[-1]["songs"] = song_ids

    print("Done fetching all", len(found_songs.keys()), "individual songs.")
    print("Fetched songs ids from all songs in", time.time()-start_time, "s!")
    if(not_found_songs != []):
        with open("not_found_songs.json", "w") as json_file:
            json_file.write(json.dumps(not_found_songs, indent=4))
    return output

def like_all_songs(songs):
    print("Do you want me to like all the songs in your 'favorite songs' playlist, so that they appear in youtube's automatically generated playlist?")
    input = input("enter 'y' for yes, anything else for no")
    if(input in ["y", "Y", "yes", "Yes"]):
        for song in songs:
            ytmusic.rate_song(song, "LIKE")

def create_all_playlists(playlists):
    print("Creating all playlists in yt music.")
    i = 0
    while i < len(playlists):
        playlist = playlists[i]
        try:
            ytmusic.create_playlist(
                playlist["name"].replace("<", "(").replace(">", ")"),     # for whatever reason these symbols arent allowed in playlist names
                playlist["description"],
                video_ids = playlist["songs"]
            )
            print("Created playlist", playlist["name"])
            if(playlist["name"]=="your favorites from spotify"):
                like_all_songs(playlist["songs"])
            i+=1
        except:
            print("You tried to create too many playlists, yt music only allows you to create 25 playlists every 6h.")
            with open("remaining.json", "w") as json_file:
                json_file.write(json.dumps(yt_playlists[i:], indent=4))
            print("To add the remaining playlists, just rerun this program in 6h. The remaining playlists are saved in the file remaining.json")
            i = len(yt_playlists)

def print_not_added_songs():
    if(os.path.isfile("not_found_songs.json")):
        with open("not_found_songs.json") as json_file:
            not_found_songs = json.load(json_file)
            print("Couldnt find the following song:")
            for playlist in not_found_songs:
                for playlist_name, songs in playlist.items():
                    print("-----", playlist_name, "-----")
                    for song in songs:
                        print("-", song)
        print("This has been saved for later use in the file not_found_songs.json")

# --------------
# PROGRAMM START
# --------------

total_time = time.time()

# skip fetching playlists if they have already been fetched
if(os.path.isfile("remaining.json") or os.path.isfile("yt_playlists.json")):
    yt_playlists = []
    if(os.path.isfile("remaining.json")):
        with open("remaining.json") as json_file:
            yt_playlists = json.load(json_file)
            print("Loaded remaining playlists from file.")
    else:
        with open("yt_playlists.json") as json_file:
                yt_playlists = json.load(json_file)
                print("Loaded yt music playlists from file.")        
    create_all_playlists(yt_playlists)
else:   # start fetching needed data
    # get or generate yt music credentials
    print("Getting yt music credentials...")
    if(not os.path.isfile("oauth.json")):
        print("generating youtube api tokens, please follow the instructions:")
        oauth = ytmusicapi.setup_oauth(open_browser = True)
        with open("oauth.json", "w") as json_file:
            json_file.write(json.dumps(oauth, indent=4))
    ytmusic = YTMusic("oauth.json")

    start_time = time.time()

    # get all the users playlists from spotify
    print("Finding all playlists on spotify...")
    playlists = []
    if(os.path.isfile("spotify_playlists.json")):
        with open("spotify_playlists.json") as json_file:
            playlists = json.load(json_file)
            print("Loaded spotify playlists from file.")
    else:
        print("Getting spotify credentials...")
        credentials = {}
        with open("credentials.json") as json_file:
            credentials = json.load(json_file)
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                            scope = "user-library-read",
                            client_id = credentials["spotify_client_id"],
                            client_secret = credentials["spotify_client_secret"],
                            redirect_uri = "http://localhost:3000"))

        playlists = find_all_spotify_playlists(sp)
        print("Finished fetching all playlists from spotify!")
        total_songs=0
        for playlist in playlists:
            total_songs += len(playlist["songs"])
        print("Fetched", len(playlists), "playlists containing a total of", total_songs, "songs in", time.time()-start_time, "s.")
        with open("spotify_playlists.json", "w") as json_file:
                json_file.write(json.dumps(playlists, indent=4))

    # create new playlists in youtube music
    yt_playlists = get_all_ytm_ids(playlists)
    with open("yt_playlists.json", "w") as json_file:
        json_file.write(json.dumps(yt_playlists, indent=4))
    create_all_playlists(yt_playlists)
    print_not_added_songs()

print("Finished in", time.time() - total_time, "s.")