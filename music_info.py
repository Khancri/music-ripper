import pylast

API_KEY = "91a287c39bf3d79f1ce589bd6165bc62"
API_SECRET = "183dbc9750acb76dbd267ec43ee2db2f"

# connect
network = pylast.LastFMNetwork(
		api_key=API_KEY,
		api_secret=API_SECRET,
		username="BenpaiWasTaken"
)

track = network.get_track("juice wrld", "armed and dangerous")

# basic info
print(track.get_duration()/1000)      # duration in milliseconds
print(track.get_playcount())     # total last.fm plays
print(track.get_wiki_summary())  # little blurb about the song

# tags/genres (returns a list of TopItem objects)
tags = track.get_top_tags(limit=5)
for tag in tags:
	print(tag.item.get_name()) # e.g., "art rock", "electronic"