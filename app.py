import spotipy, random
import numpy as np
import pandas as pd
import csv
import editdistance
from sklearn import cross_validation as cv
from sklearn.metrics.pairwise import pairwise_distances
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.metrics import mean_squared_error
from math import sqrt
from sklearn.neighbors import KDTree

user_dict ={}
track_dict ={}

DEBUG = False

np.set_printoptions(precision=3)

# CSV headers
header = ['user', 'track_id', 'rating', 'track_name', 'artist', 'acousticness',
        'danceability', 'duration_ms', 'energy', 'instrumentalness', 'key',
        'liveness', 'loudness', 'mode', 'speechiness', 'tempo',
        'time_signature', 'valence', 'preview_url']

def add_song_base(user, songs):
    with open('songs.csv', 'a+') as csvfile:
        song_writer = csv.DictWriter(csvfile, fieldnames= header)
        user_id= -1
        if user_dict.get(user) == None:
            user_dict[user] = len(user_dict)
            user_id= user_dict[user]
        else:
            user_id= user_dict.get(user)
        for song in songs:
            af= song.audio_features
            if af != None:
                track_id= -1
                if track_dict.get(af.track_id) == None:
                    track_dict[af.track_id]= len(track_dict)
                    track_id= track_dict[af.track_id]
                else:
                    track_id= track_dict[af.track_id]
                preview_url = ''
                if song.preview_url is not None:
                    preview_url = song.preview_url
                song_writer.writerow({
                    'user': user_id,
                    'track_id':track_id,
                    'rating':int(random.randint(1,5)),
                    'track_name':str(song.title),
                    'artist':str(song.artist),
                    'acousticness':af.acousticness,
                    'danceability':af.danceability,
                    'duration_ms':af.duration_ms,
                    'energy':af.energy,
                    'instrumentalness':af.instrumentalness,
                    'key':af.key,
                    'liveness':af.liveness,
                    'loudness':af.loudness,
                    'mode':af.mode,
                    'speechiness':af.speechiness,
                    'tempo':af.tempo,
                    'time_signature':af.time_signature,
                    'valence':af.valence,
                    'preview_url':preview_url
                })

class Track:
    def __init__(self, id, user, title, artist, playlist = None, audio_features = None, preview_url = None):
        self.id = id
        self.user = user
        self.title = title
        self.artist = artist
        self.playlist = playlist
        self.audio_features = audio_features
        self.preview_url = preview_url

    def __str__(self):
        audio_features = preview_url = ''
        if self.audio_features is not None:
            audio_features = str(self.audio_features)
        if self.preview_url is not None:
            preview_url = '<button class="preview_play" data-url="' + self.preview_url + '">Play</button>'
        return '<tr><td>'+str(preview_url)+'</td><td>'+self.title+'</td><td>'+self.artist+'</td>'+audio_features+'</tr>'

    def setAudioFeatures(self, audio_features):
        self.audio_features = audio_features

class AudioFeatures:
    def __init__(self, result):
        if 'id' in result:
            self.track_id = result['id']
        else:
            self.track_id = result['track_id']
        self.acousticness = float(result['acousticness'])
        self.danceability = float(result['danceability'])
        self.duration_ms = int(result['duration_ms'])
        self.energy = float(result['energy'])
        self.instrumentalness = float(result['instrumentalness'])
        self.key = int(result['key'])
        self.liveness = float(result['liveness'])
        self.loudness = float(result['loudness'])
        self.mode = int(result['mode'])
        self.speechiness = float(result['speechiness'])
        self.tempo = float(result['tempo'])
        self.time_signature = int(result['time_signature'])
        self.valence = float(result['valence'])

    def __str__(self):
        return '<td>'+str(round(self.acousticness,4))+'</td><td>'+ \
            str(round(self.danceability,4))+'</td><td>'+ \
            str(self.duration_ms)+'</td><td>'+ \
            str(round(self.energy,4))+'</td><td>'+ \
            str(round(self.instrumentalness,4))+'</td><td>'+ \
            str(self.key)+'</td><td>'+ \
            str(round(self.liveness,4))+'</td><td>'+ \
            str(round(self.loudness,4))+'</td><td>'+ \
            str(self.mode)+'</td><td>'+ \
            str(round(self.speechiness,4))+'</td><td>'+ \
            str(round(self.tempo,4))+'</td><td>'+ \
            str(self.time_signature)+'</td><td>'+ \
            str(round(self.valence,4))+'</td>'
    
    def toList(self):
        return [self.acousticness, self.danceability, self.duration_ms, \
                self.energy, self.instrumentalness, self.key, self.liveness, \
                self.loudness, self.mode, self.speechiness, self.tempo, \
                self.time_signature, self.valence]

def process_tracks(user, tracks, playlist):
    track_objects = []
    for item in tracks['items']:
        track = item['track']
        track_objects.append(Track(track['id'], user, track['name'], track['artists'][0]['name'], playlist, None, track['preview_url']))
    return track_objects

def to_str_key(l):
    str_key = ""
    for i in range(len(l)):
        str_key = str_key + str(l[i])
    return str_key

def makeTrackTable(track_objects):
    content = '<table class="track_table"><tr><th>Preview</td><th>Title</th><th>Artist</th>'+ \
                '<th>Acousticness</th><th>Danceability</th><th>Duration (ms)</th><th>Energy</th>'+ \
                '<th>Instrumentalness</th><th>Key</th><th>Liveness</th><th>Loudness</th>'+ \
                '<th>Mode</th><th>Speechiness</th><th>Tempo</th><th>Time Signature</th>'+ \
                '<th>Valence</th></tr>'
    for track in track_objects:
        content += str(track)
    content += '</table>'
    return content

def trackFromCSVRow(row):
    preview_url = None
    if isinstance(row['preview_url'], str) and row['preview_url'] != '':
        preview_url = row['preview_url']
    
    return Track(row['track_id'], row['user'], row['track_name'], \
                  row['artist'], None, AudioFeatures(row), preview_url)

from flask import Flask, redirect, url_for, request
app = Flask(__name__, static_url_path='/static')
@app.route('/', methods = ['GET'])
def main_page():
    link_rel = '<link rel="stylesheet" type="text/css" href="'+ url_for('static', filename='styles.css') + '" />'
    script = '<script type="text/javascript" src="' + url_for('static', filename='script.js') + '"></script>'

    html = """<html>
            <head>
                <title>Spotify Music Recommender</title>"""
    html += link_rel
    html += '<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>'
    html += script
    html += """</head>
            <body>
                <h1>Spotify Music Recommender</h1>
                <h3>CS 4701 Project - The Recommenders: Alexander Strandberg (ads286), Joseph Nechleba (jdn64), Jieun Kim (jk2562), Tracy Goldman (tag96), and Yuxin Xu (yx67)</h3>
                <form action="/collaborative" method="GET" id="collaborative_form">
                    <p>Enter Spotify Username to View Recommendations Using Collaborative Filtering:</p>
                    <p><input type="text" name="username" /><input type="submit" value="Go" /></p>
                </form>
                <form action="/k-nearest" method="GET" id="k-nearest_form">
                    <p>Enter a Song Title to View Recommendations Using K-Nearest Neighbors:</p>
                    <p><input type="text" name="title" /><input type="submit" value="Go" /></p>
                </form>
                <div>
                    <div id="collaborative_div"></div>
                    <div id="k-nearest_div"></div>
                </div>
            </body>
        </html>"""
    return html

@app.route('/collaborative', methods = ['GET'])
def collaborative_filtering():
    content = '<h2>Collaborative Filtering Recommendations</h2>'
    username = request.args.get('username')
    if username is not None:
        track_objects = []
        # fetch all the user's playlists, along with the tracks in them
        playlists = sp.user_playlists(username)
        for playlist in playlists['items']:
            results = sp.user_playlist(playlist['owner']['id'], playlist['id'],
                fields='tracks,next')
            tracks = results['tracks']
            track_objects.extend(process_tracks(username, tracks, playlist['name']))
            while tracks['next']:
                tracks = sp.next(tracks)
                track_objects.extend(process_tracks(username, tracks, playlist['name']))
        # now fetch the audio features for every track
        fetch_limit = 50
        audio_features = []
        usable_tracks = []
        for i in range(0, len(track_objects), fetch_limit):
            tracks = track_objects[i:i+fetch_limit]
            track_ids = []
            for track in tracks:
                if track.id is not None:
                    track_ids.append(track.id)
                    usable_tracks.append(track)

            results = sp.audio_features(track_ids)
            audio_features.extend(results)
        
        for i in range(0, len(usable_tracks)):
            if audio_features[i] is not None:
                usable_tracks[i].setAudioFeatures(AudioFeatures(audio_features[i]))
        
        tracks_with_audio_features = []
        for track in usable_tracks:
            if track.audio_features is not None:
                tracks_with_audio_features.append(track)

        if DEBUG:
            content = '<h2>Songs for ' + username + ':</h2>'
            content += makeTrackTable(tracks_with_audio_features)
        
        add_song_base(username, tracks_with_audio_features)
        df = pd.read_csv('songs.csv', sep=',', names=header)
        n_users = df.user.unique().shape[0]
        n_items = df.track_id.unique().shape[0]
        if DEBUG:
            content += '<p>Number of users = ' + str(n_users) +\
                ' | Number of songs = ' + str(n_items) + '</p>'
        train_data, test_data = cv.train_test_split(df, test_size=0)
        train_data_matrix = np.zeros((n_users, n_items))

        #NOW DO RATING REC
        for index, row in df.iterrows():
            train_data_matrix[row['user'], row['track_id']] = row['rating']
        test_data_matrix = np.zeros((n_users, n_items))
        user_similarity = pairwise_distances(train_data_matrix,metric='cosine')
        if DEBUG:
            content += '<pre>' + str(user_similarity) + '</pre>'
        min_diff= 1
        #index of the user that just typed their id in
        current_user_index= len(user_similarity)-1
        #index of user most similar to this user
        most_similar_user_index= current_user_index
        #values of similarity array associated with this user
        similarity_vals= user_similarity[current_user_index]
        #find the smallest non zero value in the similarity matrix, this 
        #should coresspond to the user with the most similar ratings
        #get that user's id (index in the matrix)
        for i in range(len(similarity_vals)):
            diff= similarity_vals[i]
            if diff > 0 and diff <= min_diff:
                min_diff= diff
                most_similar_user_index= i
        if DEBUG:
            content += "<p>most similar user index is: " + str(most_similar_user_index) + '</p>'
        #then pull 20 songs from that user's playlists
        with open('songs.csv', newline='') as csvfile:
            songreader = csv.DictReader(csvfile, fieldnames= header)
            #print out the first twenty songs from the recommended user's data
            #that are ranked 5
            count= 0

            tracks_to_print = []
            for row in songreader:
                if int(row['user']) == most_similar_user_index and int(row['rating']) == 5:
                    track = trackFromCSVRow(row)
                    tracks_to_print.append(track)
                    count += 1
                    if count == 20:
                        break
            
        content += makeTrackTable(tracks_to_print)
    return content

@app.route('/k-nearest', methods = ['GET'])
def k_nearest():
    content = '<h2>K-Nearest Recommendations</h2>'
    title = request.args.get('title')

    if title is not None:
        df = pd.read_csv('songs.csv', sep=',', names=header)
        n_users = df.user.unique().shape[0]
        n_items = df.track_id.unique().shape[0]
        if DEBUG:
            content += '<p>Number of users = ' + str(n_users) +\
                ' | Number of songs = ' + str(n_items) + '</p>'
        train_data_full, test_data_empty = cv.train_test_split(df, test_size=0)
        X = []
        track_unique_list = []
        track_list = []
        index_of_song_to_rec = None
        rec_track_info = ''
        lowest_edit_distance = -1
        for index, row in df.iterrows():
            #keep track of what song this is
            unique_track_id = row['track_name'] + row['artist']
            if not unique_track_id in track_unique_list:
                #add song name to name_list
                track = trackFromCSVRow(row)
                track_list.append(track)
                track_unique_list.append(unique_track_id)

                #add valences to X
                X.append(track.audio_features.toList())

                #check if entered song title matches this track
                distance = editdistance.eval(title.lower(), track.title.lower())
                if title.lower() in track.title.lower() and (lowest_edit_distance == -1 or \
                    distance < lowest_edit_distance):
                    index_of_song_to_rec = len(X) - 1
                    rec_track_info = track.title + ' - ' + track.artist
                    lowest_edit_distance = distance
        
        if index_of_song_to_rec is not None:
            tree = KDTree(X, leaf_size=2)
            dist, ind = tree.query([X[index_of_song_to_rec]], k=11)
            #print out the recs
            tracks_to_print = []
            for x in np.nditer(ind):
                tracks_to_print.append(track_list[x])
            
            content += '<h3>Song: ' + rec_track_info + '</h3>'
            content += makeTrackTable(tracks_to_print)
            if DEBUG:
                content += "Distance from Entered Song: "+str(dist)
        else:
            content += '<p>Song not found. Please try again.</p>'

    return content

client_credentials_manager = SpotifyClientCredentials(client_id =
                                                      '418a5497c83c448d9edcc219d9fce50b',
                                                      client_secret =
                                                      '6c2c9a1b9f374338bf9a525fba167f42')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

if __name__ == '__main__':
    app.run()
