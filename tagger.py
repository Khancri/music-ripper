import mimetypes
import requests
import pylast
from mutagen.mp3 import MP3
import mutagen.id3 as id3
import os;
from dotenv import load_dotenv
load_dotenv('.env')
API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']

network = pylast.LastFMNetwork(
		api_key=API_KEY,
		api_secret=API_SECRET,
		username="BenpaiWasTaken"
)



def tag_file(file_path, artist, song):
	tags = MP3(file_path)
	# connect

	# usage

	track = network.get_track(artist, song);
	track_album = track.get_album()
	tags['TIT2'] = id3.TIT2(encoding=3, text=track.get_title(True))

	try:
		tags['TALB'] = id3.TALB(encoding=3, text=track_album.get_title(True))
		url = track_album.get_cover_image()
		print(url)
		response = requests.get(url)
		# print(track.get_album().get_release_date())
		if response.status_code == 200:
			tags.tags.delall('APIC')
			tags.tags.add(
				id3.APIC(
					encoding=3,       # 3 is for UTF-8
					mime=mimetypes.guess_type(url)[0], # image/jpeg or image/png
					type=3,           # 3 is for the Front Cover
					desc=u'Cover',    # Description
					data=response.content
				)
			)
	except:
		pass
	tags['TPE1'] = id3.TPE1(encoding=3, text=track.get_artist().get_name(True))

	# tags['APIC'] = id3.APIC(encoding=3, )

	tags.tags.update_to_v23()
	print(tags.tags.version)
	tags.save()

if __name__ == "__main__":
	tag_file(input('file: '), input('artist: '), input('track name: '))