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
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
from numpy.polynomial.polynomial import polyfit


from spotipy.oauth2 import SpotifyClientCredentials
client_credentials_manager = SpotifyClientCredentials(client_id='58594f38045e4e0389f0e52dca5df990', client_secret='e8acf222626b4f129cde3a55778e66e6')
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

artist_link = 'https://open.spotify.com/artist/2YZyLoL8N0Wb9xBt1NhZWg?si=SQiikVJ4Qk-SZQx4O3pJFQ' #kendrick lamar

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
    for i in range (0,len(song_list)):
        popularity = i + 1
        return_list.append((song_list[i], album_list[i], popularity, time_list[i]))

    # print("Apple Top Songs Info List:")
    # print(return_list)
    # print('\n')
    return return_list

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
        album_tracks = sp.album_tracks(album_id = album_id, limit = 25)
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


    for list in info_lst:
        for song in song_name_lst:
            if list[0] == song[1]:
                list[0] = song[0]
    # print("ArtistData Info List:")
    # print(info_lst)
    # print('\n')
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
    
    # print("Spotify Popularity Info List:")
    # print(song_pop)
    # print('\n')
    return song_pop


def spotipyDBSetUp(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS Spotipy_Info")
    cur.execute('CREATE TABLE Spotipy_Info (name TEXT, danceability INTEGER, energy INTEGER)')
    lst = ArtistData(artist_link)
    for item in lst:
        cur.execute("INSERT OR IGNORE INTO Spotipy_Info (name, danceability, energy) VALUES (?,?,?)" ,
        (item[0],item[1],item[2]))
    conn.commit()

def SongPopdbSetUp(db_name):
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

def appleDBSetUp(db_name, data):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    # cur.execute("DROP TABLE IF EXISTS Apple_Info")
    cur.execute("CREATE TABLE IF NOT EXISTS Apple_Info(name TEXT, album TEXT, popularity INTEGER, time INTEGER)")
    lst = data
    count = 0
    for item in lst:
        if count == 10:
            print("10 items added, run the program again to add more")
            break
        current_name = item[0]
        cur.execute("SELECT * FROM Apple_Info WHERE name= ?", (current_name,))
        try:
            data = cur.fetchone()[0]
            continue
        except:
            cur.execute("INSERT OR IGNORE INTO Apple_Info (name, album, popularity, time) VALUES (?,?,?,?)", (item[0],item[1],item[2],item[3]))
            count += 1 
    conn.commit()

    
def joinDBs(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    #joining danceability and length of song databases with apple and spotipy databases
    cur.execute("""SELECT Spotipy_Info.danceability, Apple_Info.time, Apple_Info.popularity, Apple_Info.album, Apple_Info.name
    FROM Spotipy_Info
    JOIN Apple_Info
    ON Spotipy_Info.name = Apple_Info.name
    """)
    results = cur.fetchall()
    return results

def calculations_alb_dance(calc_lst, filename):   
    #calc_lst is the return list from joindb function
    # (dancibility, song_length, popularity, album, song)
    album_lst = []
    d = {}
    count = 0
    length_count = 0

    album_length = sum(i[1] for i in calc_lst)
    for item in calc_lst:
        dance = item[0]
        length = item[1]
        album = item[3]
        if album not in d.keys():
                d[album] = [round(dance,2), length]
                
        else:
            d[album][0] += round(dance,2)
            d[album][1] += length
    # [album] = [dance, length]

    for key in d:
        d[key] = round((d[key][0] / d[key][1]), 4)

    album_lst = []
    calc_lst = []

    for key in d:
        album_lst.append(key)
        calc_lst.append(d[key])

    with open(filename, 'w') as f:
        f.write("Format = Album Name: Danceability Per Second of Album")
        f.write('\n')
        for key in d:
            f.write(key + ": " + str(d[key]))
            f.write('\n')
    
    return (album_lst, calc_lst)

def visualization_alb_dnc(input_tup):
    #takes in return tuple from calculations_alb_dance function
    plt.bar(input_tup[0], input_tup[1], color=(.5, .3, .7), edgecolor='black')
    plt.ylabel('Danceability Per Second')
    plt.xlabel('Album Name')
    plt.title("Danceability per Second of Kendrick Lamar's Top Albums")
    plt.show()

def calculations_pop_dnc_corr(calc_lst): 
    # (dancibility, song_length, popularity, album, song)
    calc_lst_srt = sorted(calc_lst, key=lambda tup: tup[0])
    pop_lst = []
    dance_lst = []
    for item in calc_lst_srt:
        pop_lst.append(item[2])
        dance_lst.append(item[0])

    return (pop_lst, dance_lst)


def visualization_pop_dnc_corr(input_tup):
    # Generate data
    x = np.array(input_tup[1]) #danceability list
    y = np.array(input_tup[0]) #popularity list

    a, b = np.polyfit(x, y, 1)
    plt.plot(x, y, '.')
    plt.plot(x, a*x+b)
    plt.ylabel('Song Popularity')
    plt.xlabel('Song Danceability')
    plt.title("Song Popularity to Danceability Correlation")
    plt.show()

def visualization_dance_pop(artistlink):
    info_lst = ArtistData(artistlink)
    sorted_info_lst = sorted(info_lst, key = lambda x:x[2])
    dance_vals = []
    energy_vals = []
    annotations = []
    for item in sorted_info_lst:
        dance_vals.append(item[1])
        energy_vals.append(item[2])
        annotations.append(item[0])
    x = np.array(dance_vals)
    y = np.array(energy_vals)

    plt.scatter(x, y)
    plt.ylabel('Song Energy Level')
    plt.xlabel('Song Danceability Level')
    plt.title("Kendrick Lamar Song Energy Level vs Danceability Level")
    plt.rcParams['font.size'] = 5
    for i, label in enumerate(annotations):
        plt.annotate(label, (x[i], y[i]))
    plt.show()

def album_pop(db_name, data):
    data = joinDBs(db_name)
    sorted_data = sorted(data, key=lambda x:x[3])
    album_lst = []
    pop_lst = []

    for item in sorted_data:
        album_lst.append(item[3])
        pop_lst.append(item[2])
     
    
    # plot lines
    plt.bar(album_lst, pop_lst, color = (.25, .94, .60))
    plt.ylabel('popularity')
    plt.xlabel('album')
    plt.title("popularity of albums")
    plt.show()


def main():

    lst = getTopSongsApple()
    ArtistData(artist_link)
    SongPopData(artist_link)
    SongPopdbSetUp('spotipy_apple_final.db')
    appleDBSetUp('spotipy_apple_final.db', lst)
    spotipyDBSetUp('spotipy_apple_final.db')
    joinDBs('spotipy_apple_final.db')
    calc_lst = joinDBs('spotipy_apple_final.db')
    vis_tup_1 = calculations_alb_dance(calc_lst, 'final_calculations.txt')
    visualization_alb_dnc(vis_tup_1)
    vis_tup_2 = calculations_pop_dnc_corr(calc_lst)
    visualization_pop_dnc_corr(vis_tup_2)
    visualization_dance_pop(artist_link)
    album_pop('spotipy_apple_final.db', calc_lst)

if __name__ == "__main__":
    main()
