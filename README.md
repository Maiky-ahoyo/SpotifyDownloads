# A Python script to download Spotify playlists as MP3 files from YouTube with metadata.

## Usage Instructions

### 1. Register a Spotify Application:

[Go to Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)

1. Create a new application
2. Get your **Client ID** and **Client Secret**
3. Replace `your-client-id` and `your-client-secret` in the code

### 2. Install Required Dependencies:

```cmd
pip install spotipy yt-dlp mutagen requests python-dotenv
```

### 3. Install FFmpeg:

- **Windows**: [Windows build](https://www.gyan.dev/ffmpeg/builds/)
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`
  Add it to your system PATH

### 4. YouTube Cookies Setup:

1. Install the "Get cookies.txt" Chrome extension
2. Log in to YouTube in your browser
3. Export cookies as cookies.txt and place it in the project directory

### 5. Run the Script:

```cmd
python spotify_downloader.py "PLAYLIST_URL" "DESTINATION_DIRECTORY"
```

## ▲ Features ▲

- ▶ MP3 downloads with metadata
- ▶ Smart duplicate detection
- ▶ Automatic YouTube search
- ▶ Album art integration

## Notes

Audio quality depends on YouTube availability

Some songs might not match perfectly

Download speed depends on internet connection

First run might take longer due to metadata processing

## Configuration

Create a .env file with:

```cmd
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

## Recommended Workflow

1. Create virtual environment
2. Install dependencies
3. Set up cookies.txt
4. Configure .env file
5. Run with playlist URL
