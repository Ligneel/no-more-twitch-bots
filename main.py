import logging
from multiprocessing import RLock
from threading import Thread
import sys
import time

import requests
from irc.bot import SingleServerIRCBot

USERNAME = 'A MOD OF YOUR CHANNEL'
CHANNEL = 'YOUR CHANNEL'
CLIENT_ID = 'q6batx0epp608isickayubi39itsckt'
TOKEN = 'GET ONE IN https://twitchapps.com/tmi/'
DEBUG = False
WHITELIST = ['streamelemenmts', 'nightbot', 'moobot']
THRESHOLD = 300

class TwitchBotBan(SingleServerIRCBot):
    def __init__(self):
        # Fetching channel ID
        print("Fetching Channel ID...")
        url = 'https://api.twitch.tv/helix/users?login=' + CHANNEL
        headers = {'Client-ID': CLIENT_ID, 'Authorization': f'Bearer {TOKEN}'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['data'][0]['id']
        self.lock = RLock()
        self.channel = CHANNEL

        # Connect to IRC
        print("Connecting to IRC...")
        server = 'irc.chat.twitch.tv'
        port = 6667
        SingleServerIRCBot.__init__(self, [(server, port, 'oauth:' + TOKEN)], USERNAME, USERNAME)

    def on_welcome(self, c, e):
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        print("Chatbot started, fetching mod users")

        r = requests.get('https://api.twitchinsights.net/v1/bots/all').json()
        lst = list(filter(lambda x: x[1] > THRESHOLD, r['bots']))
        for idx, entry in enumerate(lst):
            self.ban(entry[0], idx, len(lst))
        print("Process complete")
        sys.exit(0)

    def ban(self, username, idx, len):
        if username in WHITELIST:
            print("Refused to ban " + username)
            return
        with self.lock:
            self.connection.privmsg(self.channel, "/ban " + username)
        print("Banned {} ({}/{})".format(username, str(idx), len))
        time.sleep(0.5)

    def unban(self, username):
        self.connection.privmsg(self.channel, "/unban " + username)

    def on_disconnect(self, c, e):
        print("Disconnected from IRC.")

    def on_join(self, c, e):
        print(f"Joined {e.target}.")

    def on_error(self, c, e):
        print(f"Error: {e.target}, {e.source}, {e.arguments}")

if __name__ == "__main__":
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)

    print("Initializing...")

    bot = TwitchBotBan()

    thread = Thread(target=bot.start)
    thread.daemon = True

    try:
        thread.start()
        while thread.is_alive():
            thread.join(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
