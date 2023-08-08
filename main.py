import openai
import time
import dotenv
import os
import json

from spotify import SpotifyPlaylistParser
from rich.prompt import Prompt
from rich.console import Console


class SpotifyInformationGatheringChat:
    DELIMITER = "####"

    SYSTEM_PROMPT = f"""
    You are a friendly chatbot helping to find new songs for playlists.
    Proceed as follows:

    1. introduce yourself and say what you can help with. Ask the user what his/her name is.
    2. ask what kind of music the user likes best.
    3. ask the user for an existing playlist by asking for the URL for a Spotify playlist.
    4. do not ask another question or answer to the response. Instead, you must summarize the user's input by returning a JSON. The JSON has the fields "name", "musicgenre", and "playlistURL". Return the JSON as a correctly formatted JSON object. You must output only the JSON. Do not reply with any other text.
    
    You must address the user by name in each of your messages once you learn the name.
    Always be friendly and do not suggest offensive songs.
    Reply with no more than three sentences. Write only in German. The user input is marked as delimiter by {DELIMITER}
    """

    def __init__(self) -> None:
        self.messages = [
            {"role": "system", "content": SpotifyInformationGatheringChat.SYSTEM_PROMPT}
        ]  # Chat-Historie

    def chat(self, userprompt):
        userprompt = userprompt.replace(SpotifyInformationGatheringChat.DELIMITER, "")
        self.messages.append(
            {
                "role": "user",
                "content": f"{SpotifyInformationGatheringChat.DELIMITER}{userprompt}{SpotifyInformationGatheringChat.DELIMITER}",
            }
        )
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613", messages=self.messages, temperature=0
        )
        self.messages.append(chat_completion.choices[0].message)
        return chat_completion.choices[0].message.content


class SpotifySongSuggester:
    DELIMITER = "####"

    SYSTEM_PROMPT_WITH_SPOTIFY = """
    You are a friendly chatbot helping to find new songs to add to a playlists for a user.
    
    The user likes {MUSIC_GENRE} music. You must not ask for the user's favourite genre again!

    Additionally, we know that the user has already the following songs on the playlist:

    {PLAYLIST}

    The user's name is {NAME}.

    Suggest new songs based on the selected music genre and already added songs on the playlist.
    Do not recommend songs which are already on the playlist.
    Do not recommend songs twice.
    Do only recommend songs which you know.
    Recommend at least three songs in every response.
    Separate each of the songs with a new line character.
    For example:

    Green Day - Basket Case
    Empire of the Sun - Walking On A Dream
    Pixies - Where Is My mind?

    You must address the user by name in each of your messages.
    Always be friendly and do not suggest offensive songs.
    Reply with no more than five sentences. Write only in German. The user input is marked as delimiter by {DELIMITER}
    """

    SYSTEM_PROMPT_WITHOUT_SPOTIFY = """
    You are a friendly chatbot helping to find new songs to add to a playlists for a user.
    
    The user likes {MUSIC_GENRE} music. You must not ask for the user's favourite genre again!
    The user's name is {NAME}.

    Suggest new songs based on the selected music genre.
    Do not recommend songs twice.
    Do only recommend songs which you know.
    Recommend at least three songs in every response.
    Separate each of the songs with a new line character.
    For example:

    Green Day - Basket Case
    Empire of the Sun - Walking On A Dream
    Pixies - Where Is My mind?

    You must address the user by name in each of your messages.
    Always be friendly and do not suggest offensive songs.
    Reply with no more than five sentences. Write only in German. The user input is marked as delimiter by {DELIMITER}
    """

    def __init__(self, spotify_text, genre, name) -> None:
        template = (
            SpotifySongSuggester.SYSTEM_PROMPT_WITH_SPOTIFY
            if spotify_text and len(spotify_text) > 0
            else SpotifySongSuggester.SYSTEM_PROMPT_WITHOUT_SPOTIFY
        )
        filled_template = template.format(
            PLAYLIST=spotify_text,
            NAME=name,
            MUSIC_GENRE=genre,
            DELIMITER=SpotifySongSuggester.DELIMITER,
        )

        self.messages = [
            {
                "role": "system",
                "content": filled_template,
            }
        ]

    def chat(self, userprompt):
        userprompt = userprompt.replace(SpotifySongSuggester.DELIMITER, "")
        self.messages.append(
            {
                "role": "user",
                "content": f"{SpotifySongSuggester.DELIMITER}{userprompt}{SpotifySongSuggester.DELIMITER}",
            }
        )
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613", messages=self.messages, temperature=0
        )
        self.messages.append(chat_completion.choices[0].message)
        return chat_completion.choices[0].message.content


dotenv.load_dotenv(dotenv.find_dotenv())
openai.api_key = os.getenv("OPENAI_API_KEY")


### BLOCK 1: INFORMATIONEN SAMMELN

# Erste Kommunikation wird gemocked, damit der Bot das Gespräch eröffnet

console = Console()

spotify_information_gathering_chat = SpotifyInformationGatheringChat()
response = spotify_information_gathering_chat.chat("Hallo!")
console.print("[bold]:robot:\tBot[/bold]: ", response)

# Zuerst die Informationen erfragen
while True:
    user_input = Prompt.ask("[bold]:speaking_head:\tDu[/bold]")
    with console.status("[bold green] OpenAI wird befragt") as status:
        response = spotify_information_gathering_chat.chat(user_input)
    try:
        json_resp = json.loads(response)
        break
    except:
        pass
    console.print("[bold]:robot:\tBot[/bold]: ", response)
    time.sleep(0.5)


### BLOCK 2: NEUE SONGS VORSCHLAGEN

spotify_text = ""

if json_resp["playlistURL"].startswith("https://open.spotify.com/"):
    spotifyid = (
        json_resp["playlistURL"].split("/")[-1].split("?")[0]
    )  # TODO: ugly, but works

    # Get songs from playlist
    spp = SpotifyPlaylistParser(spotifyid)
    spotify_text = spp.get_text()

spotify_suggesting_chat = SpotifySongSuggester(
    spotify_text=spotify_text, genre=json_resp["musicgenre"], name=json_resp["name"]
)

# Erste Kommunikation wird gemocked, damit der Bot das Gespräch eröffnet
response = spotify_suggesting_chat.chat(
    "Hallo! Ich bin auf der Suche nach neuen Songs für meine Playlist."
)
console.print("[bold]:robot:\tBot[/bold]: ", response)

while True:
    user_input = Prompt.ask("[bold]:speaking_head:\tDu[/bold]")
    with console.status("[bold green] OpenAI wird befragt") as status:
        response = spotify_suggesting_chat.chat(user_input)
    console.print("[bold]:robot:\tBot[/bold]: ", response)
    time.sleep(0.5)
