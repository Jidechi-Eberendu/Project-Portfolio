#!/usr/bin/env python3
"""
Spotify Playlist Archiver - Converts playlist tracks to audio files with metadata

This utility archives Spotify playlists as audio files by locating 
corresponding YouTube content and embedding original album artwork.
"""

import os
import sys
import concurrent.futures
import urllib.request
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
import yt_dlp
from youtube_search import YoutubeSearch
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# **************REFER TO DOCUMENTATION FOR SETUP AND USAGE**************

class PlaylistArchiver:
    def __init__(self, client_id, client_secret, username):
        self.auth = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.api = spotipy.Spotify(auth_manager=self.auth)
        self.username = username

    def fetch_playlist_content(self, playlist_id):
        """Retrieve playlist metadata and track information"""
        playlist = self.api.user_playlist(
            self.username, 
            playlist_id,
            fields='tracks,next,name'
        )
        return playlist

    def extract_track_data(self, playlist):
        """Process playlist tracks into structured data"""
        tracks = []
        playlist_data = playlist['tracks']
        
        while True:
            for item in playlist_data['items']:
                track = item.get('track', item)
                try:
                    tracks.append({
                        'title': track['name'],
                        'artist': track['artists'][0]['name'],
                        'artwork': track['album']['images'][0]['url'],
                        'url': track['external_urls']['spotify']
                    })
                except (KeyError, TypeError):
                    print(f"Skipping unavailable track: {track.get('name', 'Unknown')}")
            
            if playlist_data['next']:
                playlist_data = self.api.next(playlist_data)
            else:
                break
        
        return playlist['name'], tracks

    def archive_tracks(self, playlist_name, tracks, workers=1):
        """Main processing workflow for track archival"""
        os.makedirs(playlist_name, exist_ok=True)
        metadata_path = os.path.join(playlist_name, "tracks.csv")
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            for track in tracks:
                f.write(f"{track['title']},{track['artist']},{track['url']},{track['artwork']}\n")
        
        if workers > 1:
            self._parallel_process(metadata_path, workers)
        else:
            self._process_metadata_file(metadata_path)
        
        os.remove(metadata_path)
        print("Archiving completed successfully")

    def _parallel_process(self, metadata_path, max_workers):
        """Execute processing using thread pool"""
        with open(metadata_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self._process_track, lines)

    def _process_metadata_file(self, file_path):
        """Sequential track processing"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                self._process_track(line)

    def _process_track(self, track_info):
        """Handle individual track processing"""
        data = track_info.strip().split(',')
        if len(data) < 4:
            return
            
        title, artist, _, artwork_url = data
        query = f"{artist} - {title}"
        
        try:
            yt_url = self._find_youtube_match(query)
            if not yt_url:
                print(f"No YouTube match for: {query}")
                return
                
            self._retrieve_cover(artwork_url, title)
            audio_file = self._download_audio(yt_url, title)
            self._embed_artwork(audio_file, title)
            os.remove(f"{title}.jpg")
        except Exception as e:
            print(f"Error processing {query}: {str(e)}")

    def _find_youtube_match(self, query, attempts=5):
        """Locate YouTube video for given query"""
        for _ in range(attempts):
            try:
                results = YoutubeSearch(query, max_results=1).to_dict()
                if results:
                    return "https://www.youtube.com" + results[0]['url_suffix']
            except (IndexError, KeyError):
                pass
        return None

    def _retrieve_cover(self, url, title):
        """Download album artwork"""
        try:
            with urllib.request.urlopen(url) as response:
                with open(f"{title}.jpg", 'wb') as img_file:
                    img_file.write(response.read())
        except Exception as e:
            print(f"Cover download failed for {title}: {str(e)}")

    def _download_audio(self, url, title):
        """Download and convert YouTube audio"""
        config = {
            'format': 'bestaudio/best',
            'outtmpl': f"{title}",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(config) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

    def _embed_artwork(self, mp3_path, title):
        """Embed cover art into audio file"""
        try:
            audio = MP3(mp3_path, ID3=ID3)
            try:
                audio.add_tags()
            except Exception:
                pass
            
            with open(f"{title}.jpg", 'rb') as art_file:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=art_file.read()
                    )
                )
            audio.save()
        except Exception as e:
            print(f"Metadata embedding failed for {mp3_path}: {str(e)}")


def get_config():
    """Retrieve configuration from environment or user input"""
    config = {}
    
    if os.path.isfile('settings.cfg'):
        import configparser
        parser = configparser.ConfigParser()
        parser.read('settings.cfg')
        config['id'] = parser['AUTH']['client_id']
        config['secret'] = parser['AUTH']['client_secret']
        config['username'] = parser['AUTH']['username']
    else:
        config['id'] = input("Spotify Client ID: ").strip()
        config['secret'] = input("Client Secret: ").strip()
        config['username'] = input("Username: ").strip()
    
    return config


def get_concurrency():
    """Determine processing concurrency settings"""
    core_count = os.cpu_count() or 1
    if core_count <= 1:
        return 1
        
    response = input("Enable parallel processing? [y/N]: ").lower()
    if response not in ('y', 'yes'):
        return 1
        
    try:
        workers = int(input(f"Worker threads (1-{core_count}): "))
        return max(1, min(workers, core_count))
    except ValueError:
        return 1


def main():
    print("Spotify Playlist Archiver - Initialize")
    config = get_config()
    archiver = PlaylistArchiver(
        config['id'], 
        config['secret'], 
        config['username']
    )
    
    playlist_input = input("Playlist URI or URL: ").strip()
    playlist_id = playlist_input.split('/')[-1].split('?')[0]
    
    workers = get_concurrency()
    print(f"Using {workers} worker thread{'s' if workers > 1 else ''}")
    
    playlist = archiver.fetch_playlist_content(playlist_id)
    name, tracks = archiver.extract_track_data(playlist)
    print(f"Found {len(tracks)} tracks in '{name}'")
    
    archiver.archive_tracks(name, tracks, workers)


if __name__ == "__main__":
    main()