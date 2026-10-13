import mimetypes
import re
import requests
import musicbrainzngs
from mutagen.mp3 import MP3
import mutagen.id3 as id3

musicbrainzngs.set_useragent("MusicTagger", "0.1", "joeykhan0106@gmail.com")
manual = False

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


BAD_SECONDARY = {'compilation', 'live', 'remix', 'dj-mix', 'soundtrack', 'mixtape/street', 'demo', 'interview', 'spokenword'}
PRIMARY_RANK = {'album': 0, 'ep': 1, 'single': 2}


def pick_release(releases):
    """pick the most 'original' release: official album > ep > single, no compilations/live/etc, earliest date wins"""
    def score(rel):
        rg = rel.get('release-group', {})
        primary = (rg.get('primary-type') or rg.get('type') or '').lower()
        secondary = {s.lower() for s in rg.get('secondary-type-list', [])}
        status = (rel.get('status') or 'official').lower()

        bad = (status != 'official') + len(secondary & BAD_SECONDARY)
        rank = PRIMARY_RANK.get(primary, 3)
        date = rel.get('date') or '9999'
        return (bad, rank, date)

    return min(releases, key=score) if releases else None


DURATION_TOLERANCE = 3  # seconds


def pick_recording(recordings, duration=None):
    """pick the recording whose length is closest to the youtube duration.
    only looks at recordings that matched the search about as well as the top hit,
    so a bad title match with a lucky length can't win."""
    if not recordings:
        return None
    if not duration:
        return recordings[0]

    top = max(int(r.get('ext:score', 0)) for r in recordings)
    close = [r for r in recordings if int(r.get('ext:score', 0)) >= top - 10]

    best, best_diff = None, None
    for r in close:
        if not r.get('length'):
            continue  # no length listed, can't compare
        diff = abs(int(r['length']) / 1000 - duration)
        if diff <= DURATION_TOLERANCE and (best_diff is None or diff < best_diff):
            best, best_diff = r, diff

    if best is None:
        print(f'  ⚠ nothing within {DURATION_TOLERANCE}s of {duration}s, using top search hit')
        return recordings[0]
    print(f'  length match: off by {best_diff:.1f}s')
    return best


# apple/spotify style suffixes that musicbrainz titles usually don't have
REMASTER_PATTERNS = [
    r'\s*[\(\[][^\)\]]*(remaster|re-master|mono|stereo|deluxe|anniversary|expanded|bonus)[^\)\]]*[\)\]]',
    r'\s+-\s+(\d{4}\s+)?remaster(ed)?(\s+\d{4})?.*$',
]


def clean_search_title(song):
    """strip '(2004 Remaster)' style tags so the search finds the actual song"""
    for pattern in REMASTER_PATTERNS:
        song = re.sub(pattern, '', song, flags=re.IGNORECASE)
    return song.strip() or song


def tag_file(file_path, artist, song, duration=None):
    song = clean_search_title(song)
    print(f'matching artist ({artist}) and title ({song})')
    query = f'recording:"{song}" AND artist:"{artist}" AND type:album AND NOT secondarytype:compilation'
    result = musicbrainzngs.search_recordings(query=query, limit=10)

    recordings = result.get('recording-list', [])
    if not recordings:
        result = musicbrainzngs.search_recordings(recording=song, artist=artist, limit=10)
        recordings = result.get('recording-list', [])

    if not recordings:
        print(f'⚠ no match found')
        return
    recording = None
    if manual:
        for i, record in enumerate(recordings):
            print(f'[{i+1}]: {record["title"]} - {record["artist-credit"][0]["artist"]["name"]} ({int(record.get("length", 0))/1000:.0f}s)')
        print('pick recording')
        recording = recordings[int(input())-1]
    else:
        recording = pick_recording(recordings, duration)
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
        release = pick_release(releases)
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
    manual = True
    tag_file(input('file: '), input('artist: '), input('track name: '))