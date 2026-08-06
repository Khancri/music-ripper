from mutagen.mp3 import MP3
import mutagen.id3 as id3

song = MP3("song.mp3")

song['TIT2'] = id3.TIT2(encoding=3, text='Hi there')
song['TALB'] = id3.TALB(encoding=3, text='boo')

song.save()
