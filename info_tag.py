import mimetypes
import requests
import musicbrainzngs
from mutagen.mp3 import MP3
import mutagen.id3 as id3

musicbrainzngs.set_useragent("MusicTagger", "0.1", "joeykhan0106@gmail.com")


def get_cover_art(release_id):
    url = f"https://coverartarchive.org/release/{release_id}/front"
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            return response.content, response.headers.get('Content-Type', 'image/jpeg')
    except Exception:
        pass
    return None, None


def get_track_position(release_id, recording_id):
    try:
        release_data = musicbrainzngs.get_release_by_id(release_id, includes=['recordings'])
        for medium in release_data['release'].get('medium-list', []):
            for track in medium.get('track-list', []):
                if track.get('recording', {}).get('id') == recording_id:
                    return track.get('position'), track.get('number')
    except Exception:
        pass
    return None, None


def tag_file(file_path, artist, song):
    query = f'recording:"{song}" AND artist:"{artist}" AND type:album AND NOT secondarytype:compilation'
    result = musicbrainzngs.search_recordings(query=query, limit=10)

    recordings = result.get('recording-list', [])
    if not recordings:
        result = musicbrainzngs.search_recordings(recording=song, artist=artist, limit=10)
        recordings = result.get('recording-list', [])

    if not recordings:
        print(f'⚠ no match found')
        return

    recording = recordings[0]
    print(f"  matched: {recording['title']} — {recording['artist-credit'][0]['artist']['name'] if recording.get('artist-credit') else '?'}")

    track_title = recording.get('title', song)
    track_artist = recording['artist-credit'][0]['artist']['name'] if recording.get('artist-credit') else artist

    # grab first release for album info
    releases = recording.get('release-list', [])
    album_title = None
    release_id = None
    release_year = None
    track_position = None

    if releases:
        release = releases[0]
        album_title = release.get('title')
        release_id = release.get('id')
        release_date = release.get('date', '')
        release_year = release_date[:4] if release_date else None
        track_position, _ = get_track_position(release_id, recording.get('id'))

    # write tags
    tags = MP3(file_path)
    if tags.tags is None:
        tags.add_tags()

    tags.tags['TIT2'] = id3.TIT2(encoding=3, text=track_title)
    tags.tags['TPE1'] = id3.TPE1(encoding=3, text=track_artist)

    if album_title:
        tags.tags['TALB'] = id3.TALB(encoding=3, text=album_title)
        tags.tags['TDRC'] = id3.TDRC(encoding=3, text=str(release_year))

    if track_position:
        tags.tags['TRCK'] = id3.TRCK(encoding=3, text=str(track_position))

    # cover art from cover art archive
    if release_id:
        cover_data, mime_type = get_cover_art(release_id)
        if cover_data:
            tags.tags.delall('APIC')
            tags.tags.add(id3.APIC(
                encoding=3,
                mime=mime_type,
                type=3,
                desc='Cover',
                data=cover_data
            ))
            print(f'✓ cover art found')
        else:
            print(f'⚠ no cover art found on cover art archive')

    tags.tags.update_to_v23()
    tags.save()
    print(f'✓ tagged: {track_title} by {track_artist} — {album_title or "unknown album"}')


if __name__ == "__main__":
    tag_file('song.mp3', input('artist: '), input('track name: '))