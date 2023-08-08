import spotipy
import dotenv
from spotipy.oauth2 import SpotifyOAuth

dotenv.load_dotenv(dotenv.find_dotenv())

SCOPE = ["playlist-read-private", "playlist-read-collaborative"]


class SpotifyPlaylistParser:
    def __init__(self, spotifyid) -> None:
        self.spotifyid = spotifyid

    def get_text(self):
        try:
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))
            playlist = sp.playlist_items(
                playlist_id=self.spotifyid, fields="items(track(name, artists(name)))"
            )

            return "\n".join(
                [
                    f'{song_info["track"]["artists"][0]["name"]} - {song_info["track"]["name"]}'
                    for song_info in playlist["items"]
                ]
            )
        except:
            return ""
