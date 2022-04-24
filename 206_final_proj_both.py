import string
from xml.sax import parseString
from bs4 import BeautifulSoup
from nbformat import write
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests 
import json 
import sqlite3
import os

from spotipy.oauth2 import SpotifyClientCredentials
client_credentials_manager = SpotifyClientCredentials(client_id='58594f38045e4e0389f0e52dca5df990', client_secret='e8acf222626b4f129cde3a55778e66e6')
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

artist_link = 'https://open.spotify.com/artist/2YZyLoL8N0Wb9xBt1NhZWg?si=QF3Y6Ma4QqGS-VpyFASdpw' #kendrick lamar

def getTopSongsApple():

    # returns a list with 50 tuples containing a song and its corresponding album in order of most popular song

    r = requests.get("https://music.apple.com/us/artist/kendrick-lamar/368183298/see-all?section=top-songs")
    soup = BeautifulSoup(r.text, 'html.parser')
    song_list = []
    album_list = []
    return_list = []
    artist_list = []
    time_list = []


    songs = soup.find_all('div', class_='songs-list-row__song-name')
    # artists = soup.find_all('div', class_='songs-list__col songs-list__col--artist typography-body')
    tags = soup.find_all('div', class_='songs-list__col songs-list__col--album typography-body')
    # times = soup.find_all('time', class_='songs-list-row__length')
    times = soup.find_all('time')
    
    for time in times:
        if time.has_attr('datetime'):
            time = (time.text.strip())
            time = sum(x * int(t) for x, t in zip([60, 1], time.split(":"))) 
            time_list.append(time)
    for song in songs:
        song = song.text
        song_list.append(song)
    for tag in tags:
        album = tag.find('a').text
        album_list.append(album)
    for i in range (0, 50):
        popularity = i + 1
        return_list.append((song_list[i], album_list[i], popularity, time_list[i]))

    return return_list

def appleDBSetUp(db_name, data):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS Apple_info")
    cur.execute("CREATE TABLE Apple_info(name TEXT, album TEXT, popularity INTEGER, time INTEGER)")
    lst = data
    for item in lst:
        cur.execute("INSERT OR IGNORE INTO Apple_info (name, album, popularity, time) VALUES (?,?,?,?)", (item[0],item[1],item[2],item[3]))
    conn.commit()

#getting artist data, song names, and each of their popularity levels

def ArtistData(artistlink):
    #artist info, gives me id to use for top 10 tracks
    artist = sp.artist(artistlink) #json
    artist_id = artist['id']
    artist_uri = 'spotify:artist:' + artist_id

    #top 10 track info for an artist and popularity of top 10 tracks sorted by which album theyre on 
    top_tracks = sp.artist_top_tracks(artist_id)
    track_info = top_tracks['tracks']

    track_lst = []
    d = {}
    song_pop = []
    for track in track_info[:50]:
        song_id2 = track['album']['id']
        albumname2 = track['album']['name']
        trackname = track['name']
        trackpop = track['popularity']
        song_pop.append((trackname,trackpop))
        if albumname2 not in d.keys():
            d[albumname2] = (trackname,trackpop,song_id2)
        else:
            d[albumname2] += (trackname,trackpop)
    
        track_lst.append((albumname2, trackname,trackpop,song_id2))  
    #print(song_pop)

    sorted_by_album = sorted(track_lst, key = lambda x:x[0])
    #print(sorted_by_album)

    #list of all the albums for an artist, and all of the album IDs, gives me album ids to get their tracks
    #why is it printing twice
    albums = sp.artist_albums(artist_uri, album_type='album')
    album_info = albums['items']
    #print(album_info)
    album_lst = []
    album_id_lst = []
    for album in album_info: 
        albumname = album['name']
        album_id = album['id']
        if albumname not in album_lst:
            album_lst.append(albumname) #why is there multiple copies of the same album, but each id is different
            album_id_lst.append(album_id)
    #need to sort song ids into albums they belong to

    #list of all the songs of an artist
    
    song_name_lst = []
    song_name_tup = ()
    album_track_lst = []
    album_track_dict = {}
    
    for album_id in album_id_lst:
        album_tracks = sp.album_tracks(album_id = album_id)
        song_id_lst = []
        for song in album_tracks['items']:
            song_id = song['id']
            song_name = song['name']
            song_id_lst.append(song_id)            
            song_name_lst.append((song_name, song_id))
            
        album_track_dict[album_id] = (song_id_lst) #dict with album id as key and song ids for album tracks as value
          
    #dancibility total, and separately energy total for every single song of kendrick
    songs_id_list = []
    for key in album_track_dict:
        for item in album_track_dict[key]:
            songs_id_list.append(item)

    audio_features = sp.audio_features(tracks = songs_id_list)
    
    dance_total = 0
    energy_total = 0
    info_lst = []
    info_dict = {}
    for song in audio_features:
        song_id3 = song['id']
        dance_num = song['danceability']
        energy_num = song['energy']
        info_lst.append([song_id3,dance_num,energy_num])
        # info_dict[song_id3] = (dance_num,energy_num)
        dance_total += dance_num
        energy_total += energy_num

    # id_list = list(info_dict.keys())

    # for id in id_list:
    #     for song in song_name_lst:
    #         if id == song[1]:
    #             print(song[0])
    #             info_dict[song[0]] = info_dict.pop(song[1])
    # print(info_dict)

    for list in info_lst:
        for song in song_name_lst:
            if list[0] == song[1]:
                list[0] = song[0]
    #print(info_lst)
    return info_lst


    
    #Get danceability of all songs in an album, add together, divide by number of songs for total danceability of album
    #need to get dancibility per album

def SongPopData(artist_link):
    #artist info, gives me id to use for top 10 tracks
    artist = sp.artist(artist_link) #json
    artist_id = artist['id']
    artist_uri = 'spotify:artist:' + artist_id

    #top 10 track info for an artist and popularity of top 10 tracks sorted by which album theyre on 
    top_tracks = sp.artist_top_tracks(artist_id)
    track_info = top_tracks['tracks']

    track_lst = []
    d = {}
    song_pop = []
    for track in track_info:
        song_id2 = track['album']['id']
        albumname2 = track['album']['name']
        trackname = track['name']
        trackpop = track['popularity']
        song_pop.append((trackname,trackpop))
        if albumname2 not in d.keys():
            d[albumname2] = (trackname,trackpop,song_id2)
        else:
            d[albumname2] += (trackname,trackpop)
    
        track_lst.append((albumname2, trackname,trackpop,song_id2))  
    return song_pop

def setUpSongpop(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS Song_pop")
    cur.execute ("CREATE TABLE Song_pop (name TEXT, pop INTEGER)") 
    lst = SongPopData(artist_link)
    i = 1
    for item in lst:
      cur.execute("INSERT OR IGNORE INTO Song_pop (name, pop) VALUES (?,?)", (item[0],i))
      i += 1
    conn.commit()
    cur.execute("DROP TABLE IF EXISTS Spotipy_Info")
    cur.execute('CREATE TABLE Spotipy_Info (name TEXT, danceability INTEGER, energy INTEGER)')
    lst = ArtistData(artist_link)
    for item in lst:
        cur.execute("INSERT OR IGNORE INTO Spotipy_Info (name, danceability, energy) VALUES (?,?,?)" ,
        (item[0],item[1],item[2]))
    conn.commit()


# def setUpDatabase(db_name):
#     path = os.path.dirname(os.path.abspath(__file__))
#     conn = sqlite3.connect(path+'/'+db_name)
#     cur = conn.cursor()
#     cur.execute("DROP TABLE IF EXISTS Spotipy_Info")
#     cur.execute('CREATE TABLE Spotipy_Info (name TEXT, danceability INTEGER, energy INTEGER)')
#     lst = ArtistData(artist_link)
#     for item in lst:
#         cur.execute("INSERT OR IGNORE INTO Spotipy_Info (name, danceability, energy) VALUES (?,?,?)" ,
#         (item[0],item[1],item[2]))
#     conn.commit()

# def setUptwoDatabase(db_name1, db_name2,db_name3):
#     path = os.path.dirname(os.path.abspath(__file__))
#     conn = sqlite3.connect(path+'/'+db_name3 )
#     cur = conn.cursor()
#     #joining danceability and length of song databases with apple and spotipy databases
#     cur.execute("DROP TABLE IF EXISTS Spotipy_Apple_Info")
#     cur.execute("""SELECT {db_name1}.danceability, {db_name2}.time, {db_name2}.popularity, {db_name2}.album
#     FROM {db_name1}
#     JOIN {db_name2}
#     ON {db_name1}.name = {db_name2}.name
#     """)
#     results = cur.fetchall()
#     print(results)


# def appleDBSetUp(db_name, data):
#     path = os.path.dirname(os.path.abspath(__file__))
#     conn = sqlite3.connect(path+'/'+db_name)
#     cur = conn.cursor()
#     cur.execute("DROP TABLE IF EXISTS Apple_info")
#     cur.execute("CREATE TABLE Apple_info(name TEXT, album TEXT, popularity INTEGER, time INTEGER)")
#     lst = data
#     for item in lst:
#         cur.execute("INSERT OR IGNORE INTO Apple_info (name, album, popularity, time) VALUES (?,?,?,?)", (item[0],item[1],item[2],item[3]))
#     conn.commit()
    
def joinDBs(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    #joining danceability and length of song databases with apple and spotipy databases
    cur.execute("DROP TABLE IF EXISTS Spotipy_Apple_Info")
    cur.execute("""SELECT {db_name1}.danceability, {db_name2}.time, {db_name2}.popularity, {db_name2}.album
    FROM {db_name1}
    JOIN {db_name2}
    ON {db_name1}.name = {db_name2}.name
    """)
    results = cur.fetchall()
    print(results)




def main():
    lst = getTopSongsApple()
    appleDBSetUp('Apple_info.db', lst)
    ArtistData(artist_link)
    SongPopData(artist_link)
    # setUpDatabase('Spotipy_Info.db')
    # setUpSongpop('Song_pop.db')
    setUpSongpop('Song_pop.db')

if __name__ == "__main__":
    main()

