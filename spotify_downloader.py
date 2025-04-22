import os
import sys
import time
import spotipy
import yt_dlp as youtube_dl
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TCON, delete
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_METADATA = {
    'title': 'Unknown Title',
    'artists': 'Unknown Artist',
    'album': 'Unknown Album',
    'date': 'Unknown Year',
    'genre': 'Unknown Genre',
    'image_url': None
}

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Please set the SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

def get_playlist_id(url):
    parsed = urlparse(url)
    path_segments = parsed.path.split('/')
    if 'playlist' in path_segments:
        return path_segments[path_segments.index('playlist') + 1]
    raise ValueError("Invalid playlist URL")

def get_playlist_songs(sp, playlist_id):
    songs = []
    results = sp.playlist_tracks(playlist_id)
    while results:
        for item in results['items']:
            track = item.get('track')
            if track:
                try:
                    songs.append(process_song(sp, track))
                except Exception as e:
                    print(f"Error processing track: {str(e)}")
        results = sp.next(results) if results.get('next') else None
        time.sleep(0.7)
    return songs

def process_song(sp, track):
    metadata = extract_metadata(track)
    metadata['genre'] = extract_genre(sp, track) or DEFAULT_METADATA['genre']
    return {**DEFAULT_METADATA, **metadata}

def extract_metadata(track):
    try:
        artists = ", ".join([a.get('name', '') for a in track.get('artists', []) if a.get('name')])
        artists = artists or DEFAULT_METADATA['artists']

        album_data = track.get('album', {})
        album = album_data.get('name', DEFAULT_METADATA['album'])
        date = album_data.get('release_date', '')[:4] or DEFAULT_METADATA['date']
        image_url = album_data.get('images', [{}])[0].get('url', DEFAULT_METADATA['image_url'])

        return {
            'title': track.get('name', DEFAULT_METADATA['title']),
            'artists': artists,
            'album': album,
            'date': date,
            'image_url': image_url
        }
    except Exception as e:
        print(f"Metadata extraction error: {str(e)}")
        return DEFAULT_METADATA

def extract_genre(sp, track):
    try:
        main_artist_id = track['artists'][0]['id']
        artist = sp.artist(main_artist_id)
        if artist.get('genres'):
            return artist['genres'][0].capitalize()

        album = sp.album(track['album']['id'])
        if album.get('genres'):
            return album['genres'][0].capitalize()

        return 'Unknown Genre'
    except Exception as e:
        print(f"Genre extraction error: {str(e)}")
        return DEFAULT_METADATA['genre']

def sanitize_filename(name):
    return "".join(c for c in name if c not in '\\/*?:"<>|').strip()

def song_exists(directory, song):
    expected_name = f"{sanitize_filename(song['artists'])} - {sanitize_filename(song['title'])}.mp3"
    target_path = os.path.join(directory, expected_name)

    if os.path.exists(target_path):
        try:
            audio = ID3(target_path)
            return (
                audio.get('TIT2').text[0] == song['title'] and
                audio.get('TPE1').text[0] == song['artists'] and
                audio.get('TALB').text[0] == song['album']
            )
        except:
            return False
    return False

def download_song(directory, song):
    safe_title = sanitize_filename(song['title'])
    safe_artist = sanitize_filename(song['artists'])
    final_filename = f"{safe_artist} - {safe_title}.mp3"
    final_path = os.path.join(directory, final_filename)

    if os.path.exists(final_path):
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(directory, 'temp_%(title)s.%(ext)s'),
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            }
        ],
        'writethumbnail': True,
        'ffmpeg_location': 'C:/ffmpeg/bin',
        'cookiefile': 'cookies.txt',
        'retries': 3,
        'fragment_retries': 10,
        'retry_sleep': 15,
        'ignoreerrors': True,
        'postprocessor_args': [
            '-metadata', f'title={song["title"]}',
            '-metadata', f'artist={song["artists"]}',
            '-metadata', f'album={song["album"]}',
            '-metadata', f'date={song["date"]}',
            '-metadata', f'genre={song["genre"]}',
            '-id3v2_version', '3'
        ]
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song['title']} lyrics explicit {song['artists']} ", download=True)

            if info and 'entries' in info and info['entries']:
                temp_file = ydl.prepare_filename(info['entries'][0]).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                if os.path.exists(temp_file):
                    apply_metadata(temp_file, song)
                    os.rename(temp_file, final_path)
    except Exception as e:
        print(f"Download error: {str(e)}")
        if os.path.exists(final_path):
            os.remove(final_path)

def apply_metadata(file_path, song):
    try:
        audio = ID3(file_path)
    except:
        audio = ID3()

    delete(file_path)

    audio.add(TIT2(encoding=3, text=song['title']))
    audio.add(TPE1(encoding=3, text=song['artists']))
    audio.add(TALB(encoding=3, text=song['album']))
    audio.add(TDRC(encoding=3, text=song['date']))
    audio.add(TCON(encoding=3, text=song['genre']))

    if song['image_url']:
        try:
            response = requests.get(song['image_url'], timeout=15)
            if response.status_code == 200:
                audio.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    data=response.content
                ))
        except Exception as e:
            print(f"Cover art error: {str(e)}")

    audio.save(file_path, v2_version=3)

def main(url_playlist, destination_dir):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

    try:
        os.makedirs(destination_dir, exist_ok=True)
        playlist_id = get_playlist_id(url_playlist)
        songs = get_playlist_songs(sp, playlist_id)

        for index, song in enumerate(songs):
            print(f"\nProcessing {index+1}/{len(songs)}: {song['title']}")

            if song_exists(destination_dir, song):
                print(f"Already exists: {song['title']}")
                continue

            download_song(destination_dir, song)
            time.sleep(1.5)

    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python spotify_downloader.py <playlist_url> <destination_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
