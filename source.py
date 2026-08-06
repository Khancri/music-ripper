import yt_dlp
import os
from info_tag import tag_file
from title_guess import guess_artist_title

def download_and_tag(path, url, artist, name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        }],
        'paths': {'home': path},
        'outtmpl': '%(title)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        if not os.path.exists(file_path):
            file_path = file_path.rsplit('.', 1)[0] + ".mp3"
            print(f"stored in {file_path}")
        tag_file(file_path, artist, name)
        print(f'✓ done: {name} by {artist}\n')
        return file_path


def get_playlist_entries(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # don't download, just get metadata
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            return info['entries']
        else:
            return None  # single video

def main():
    url = input('url to download: ').strip()
    path = input('save to folder [.]: ').strip() or '.'
    os.makedirs(path, exist_ok=True)

    entries = get_playlist_entries(url)

    if entries is None:
        # single track
        artist = input('artist: ')
        name = input('name: ')
        download_and_tag(path, url, artist, name)
    else:
        # playlist
        entryMeta = []
        print(f'\nfound {len(entries)} tracks in playlist\n')
        artist = None
        print('choose the number.\n1.personal playlist\n2. album\n(for albums with various artists choose playlist)')
        playlist = input(': ')
        if playlist == '2':
            artist = input('  album artist: ')
        for i, entry in enumerate(entries):
            title = entry.get('title', 'unknown')
            track_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry['id']}"

            print(f'[{i+1}/{len(entries)}] {title}')
            channel = entry.get('uploader') or entry.get('channel')
            guess_a, guess_t = guess_artist_title(title, channel)

            if playlist != '2':
                artist = input(f'  artist [{guess_a or ""}]: ').strip() or guess_a
            name = input(f'  track name [{guess_t or ""}]: ').strip() or guess_t
            
            entryMeta.append({'name': name, 'artist': artist, 'url': track_url})
        for i, entry in enumerate(entries):
            title = entry.get('title', 'unknown')

            name = entryMeta[i]['name']
            artist = entryMeta[i]['artist']
            track_url = entryMeta[i]['url']
            print(f'[{i+1}/{len(entries)}] {title}')
            if artist == "!!skip$$" or name == "!!skip$$":
                continue
            try:
                download_and_tag(path, track_url, artist, name)
            except Exception as e:
                print('something happened?? skipping and continuing\n', e)

if __name__ == '__main__':
    main()