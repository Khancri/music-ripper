import re

# junk that shows up around the actual title, strip it out first
JUNK_PATTERNS = [
    r'\(official\s*(music\s*)?video\)', r'\[official\s*(music\s*)?video\]',
    r'\(official\s*audio\)', r'\[official\s*audio\]',
    r'\(lyrics?\)', r'\[lyrics?\]',
    r'\(lyric\s*video\)', r'\[lyric\s*video\]',
    r'\(audio\)', r'\[audio\]',
    r'\(hd\)', r'\[hd\]', r'\(4k\)', r'\[4k\]',
    r'\(visualizer\)', r'\[visualizer\]',
    r'ft\..*$', r'feat\..*$',
]

SEPARATORS = [' - ', ' – ', ' — ', ' | ', ': ']


def guess_artist_title(video_title, channel_name=None):
    title = video_title.strip()

    for pattern in JUNK_PATTERNS:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    title = title.strip(' -–—|:').strip()

    for sep in SEPARATORS:
        if sep in title:
            left, right = title.split(sep, 1)
            return left.strip(), right.strip()

    # no separator found, fall back to channel name as artist guess
    if channel_name:
        channel_name = re.sub(r' - Topic', '', channel_name, flags=re.IGNORECASE)
        return channel_name.strip(), title.strip()

    return None, title.strip()


if __name__ == "__main__":
    tests = [
        ("Pierce The Veil - A Match Into Water (Official Music Video)", "Pierce The Veil"),
        ("SONG NAME | ARTIST | Lyrics", "Some Channel"),
        ("Artist: Song Title", None),
        ("just a title with no pattern", "Fallback Channel"),
    ]
    for t, ch in tests:
        print(guess_artist_title(t, ch))