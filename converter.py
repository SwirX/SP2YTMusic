import json
import os
import ytmusicapi
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from time import time
from time import sleep
from functools import reduce

def get_all_spotify_songs_from_query_result(items):
    output = []
    for song in items:    
        title = song["track"]["name"]
        for artist in song["track"]["artists"]:
            title += " " + artist["name"]
        if(title.replace(" ", "") != ""): # filter deleted songs
            output.append(title)
    return output

def find_all_spotify_songs_in_playlist(playlist_id, sp):
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
    print("fetching favorites (this may take a while)...")
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
    spotify_playlists.append(find_favorite_spotify_songs(sp))
    while(found_all == False):
        result = sp.current_user_playlists(limit=50, offset=offset)
        for item in result['items']:
            print("fetching playlist", item["name"], "...")
            songs = find_all_spotify_songs_in_playlist(item["id"], sp)
            spotify_playlists.append({
                "name" : item["name"],
                "description": item["description"],
                "songs": songs
            })
        offset += 50
        if(result["items"]==[]):
            found_all = True
    print(len(spotify_playlists), "playlists found!")
    return spotify_playlists

def get_all_ytm_ids(spotify_playlists):
    output = []
    not_found_songs = []
    found_songs = {}
    print("Looking for all your Spotify songs on YouTube Music. This will take about", 
        int(reduce(lambda x,y: x+y, map(lambda x: len(x["songs"]), spotify_playlists))*0.005),
        "minutes to complete.")
    start_time = time()
    # replace all query strings with corresponding yt music ids
    for playlist in spotify_playlists:
        song_ids = []
        not_found = []
        progress = 0

        print("Fetching YouTube Music song IDs for songs in:", playlist["name"])
        for song_title in playlist["songs"]:
            progress += 1
            if(progress % 10 == 0 or progress == len(playlist["songs"])):
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
    print("Fetched song IDs from all songs in", time()-start_time, "s.")
    if(not_found_songs != []):
        with open("not_found_songs.json", "w") as json_file:
            json_file.write(json.dumps(not_found_songs, indent=4))
    return output

def like_all_songs(songs):
    print("Do you want me to like all the songs in your 'favorite songs' playlist, so that they appear in YouTubes automatically generated playlist?")
    print("This will take a while, since YouTube has restrictions regarding how fast you can like songs.")
    confirmation = input("Enter 'y' for yes, anything else for no: ")
    if(confirmation in ["y", "Y", "yes", "Yes"]):
        counter = 1
        for song in songs[::-1]:
            counter += 1
            if(counter % 20 == 0 or counter == len(songs)):
                print(counter, "/", len(songs))
            response_check = ytmusic.rate_song(song, "LIKE")["actions"][0]["addToToastAction"]["item"]["notificationActionRenderer"]["responseText"]["runs"][0]["text"]
            while(response_check != "Saved to liked songs"):
                sleep(1)
                response_check = ytmusic.rate_song(song, "LIKE")["actions"][0]["addToToastAction"]["item"]["notificationActionRenderer"]["responseText"]["runs"][0]["text"]

def create_all_playlists(playlists_in, ytmusic):
    print("Creating YouTube Music playlists. You're almost done!")
    playlists = playlists_in[::-1] # reverse playlist, so that the oldest playlist is created first
    i = 0
    while i < len(playlists):
        playlist = playlists[i]
        try:
            ytmusic.create_playlist(
                playlist["name"].replace("<", "(").replace(">", ")"),     # for whatever reason these symbols arent allowed in playlist names
                playlist["description"],
                video_ids = playlist["songs"]
            )
            print("Created playlist", playlist["name"] + ".")
            if(playlist["name"]=="your favorites from spotify"):
                like_all_songs(playlist["songs"])
            i+=1
        except Exception as error:
            print("An error accured:", error)
            print("If you see this, it is very likely, that you tried to create too many playlists too quickly.")
            print("YouTube Music only allows you to create 25 playlists every 6h.")
            with open("remaining.json", "w") as json_file:
                json_file.write(json.dumps(playlists[i:], indent=4))
            print("To add the remaining playlists, just rerun this program in 6h. The remaining playlists are saved in the file remaining.json")
            i = len(yt_playlists)
        else:
            # empty remaining.json file
            with open("remaining.json", "w") as json_file:
                json_file.write(json.dumps([], indent=4))

def print_not_added_songs():
    if(os.path.isfile("not_found_songs.json")):
        with open("not_found_songs.json") as json_file:
            not_found_songs = json.load(json_file)
            print("Couldn't find the following song:")
            for playlist in not_found_songs:
                for playlist_name, songs in playlist.items():
                    print("-----", playlist_name, "-----")
                    for song in songs:
                        print("-", song)
        print("This has also been saved for later use in the file not_found_songs.json")

# --------------
# PROGRAMM START
# --------------

print("""
███████╗██████╗ ████████╗██████╗ ██╗   ██╗████████╗███╗   ███╗
██╔════╝██╔══██╗╚══██╔══╝╚════██╗╚██╗ ██╔╝╚══██╔══╝████╗ ████║
███████╗██████╔╝   ██║    █████╔╝ ╚████╔╝    ██║   ██╔████╔██║
╚════██║██╔═══╝    ██║   ██╔═══╝   ╚██╔╝     ██║   ██║╚██╔╝██║
███████║██║        ██║   ███████╗   ██║      ██║   ██║ ╚═╝ ██║
╚══════╝╚═╝        ╚═╝   ╚══════╝   ╚═╝      ╚═╝   ╚═╝     ╚═╝
""")
print("Welcome to SPT2YTM, the Spotify to YouTube Music converter.")
total_time = time()

# get or generate yt music credentials
print("Getting YouTube Music credentials...")
if(not os.path.isfile("oauth.json")):
    print("Generating YouTube API tokens, please follow the instructions:")
    oauth = ytmusicapi.setup_oauth(open_browser = True)
    with open("oauth.json", "w") as json_file:
        json_file.write(json.dumps(oauth, indent=4))
ytmusic = YTMusic("oauth.json")

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
    create_all_playlists(yt_playlists, ytmusic)
else:   # start fetching needed data
    start_time = time()
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
        if(os.path.isfile("credentials.json")):
            with open("credentials.json") as json_file:
                credentials = json.load(json_file)
        else:
            # create spotify credentials file
            print("Creating spotify credentials file. If you don't know where to find your spotify client id and client secret, please check the readme.md file.")
            print("Please enter the following from your app in the developer dashboard:")
            client_id = input("Enter your client id:")
            client_secret = input("Enter your client secret:")
            credentials = {
                "spotify_client_id": client_id,
                "spotify_client_secret": client_secret
            }
            with open("credentials.json", "w") as json_file:
                json_file.write(json.dumps(credentials, indent=4))

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                            scope = "user-library-read",
                            client_id = credentials["spotify_client_id"],
                            client_secret = credentials["spotify_client_secret"],
                            redirect_uri = "http://localhost:3000"))

        playlists = find_all_spotify_playlists(sp)
        with open("spotify_playlists.json", "w") as json_file:
                json_file.write(json.dumps(playlists, indent=4))
        print("Finished fetching all playlists from spotify!")
        print("Fetched", len(playlists), "playlists containing a total of", 
            reduce(lambda x,y: x+y, map(lambda x: len(x["songs"]), playlists)),
            "songs in", time()-start_time, "s.")

    # create new playlists in youtube music
    yt_playlists = get_all_ytm_ids(playlists)
    with open("yt_playlists.json", "w") as json_file:
        json_file.write(json.dumps(yt_playlists, indent=4))
    create_all_playlists(yt_playlists, ytmusic)
    print_not_added_songs()

print("Finished in", time() - total_time, "s.")
input("Press enter to close this programm.")