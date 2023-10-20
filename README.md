# spotify to yt music migration tool
This projects aims to provide a way to migrate all your playlists from spotify to youtube music.

## installation/usage
1. install [spotipy](https://spotipy.readthedocs.io/en/latest/#installation) :
    
    `pip install spotipy --upgrade`

2. install [ytmusicapi](https://ytmusicapi.readthedocs.io/en/latest/setup/index.html) :
    
    `pip install ytmusicapi`

3. setup spotify app

4. create youtube oauth.json file

## limitations
YouTubes API only allows regular users to create 25 playlists every 6 hours. For that purpose, the program creates a file `yt_playlists.json` which contains all playlists in `.json format`. If you can't create all your playlists in one go, you can edit this file and remove the playlists which have been created sucessfully earlier. Alternatively, the program asks you if you want to wait for the 6 hours before continuing. The downside being, that you need to keep your computer turned on for the 6 hours.

## dependencies
spotipy 
ytmusicapi

