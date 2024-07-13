
import asyncio
import logging
import json
from pathlib import Path
from threading import Thread

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData

logger = logging.getLogger()

class TwitchSender(Thread):
    def __init__(self, key_file, target_channel, user_scope=[AuthScope.CHAT_READ, AuthScope.CHAT_EDIT], token_cache_path=Path("credential/twitch_cache_token.json")):
        Thread.__init__(self)
        self.setDaemon(True)
        with open(key_file, "r") as key_file:
            key_data = json.load(key_file)
            self.app_id = key_data["client_id"]
            self.app_secret = key_data["client_secret"]
        self.user_scope = user_scope
        self.target_channel = target_channel
        self.token_cache_path = token_cache_path
        self.chat:Chat = None
        self.stop_req = False
        self.twitch_msg_queue = asyncio.Queue()

    def shutdown(self):
        self.stop_req = True

    def start_background_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def run(self):
        asyncio.run(self.twitch_async_run())

    def send_msg(self, msg:str):
        #TODO: Implement async send message or at least queue the message. but why the fuck async queue not have nonblocking version
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.send_twitch_msg(f"[sttntts] : {msg}"))

    async def send_twitch_msg(self, msg):
        if self.chat.is_ready() == False:
            logger.error("Twitch chat not ready yet. Skip sending message")
        else:
            await self.chat.send_message(self.target_channel, msg)

    async def __on_ready(self, ready_event: EventData):
        logger.info('Twitch chat connected')
        await ready_event.chat.join_room(self.target_channel)

    async def twitch_async_run(self):
        twitch = await Twitch(self.app_id, self.app_secret)
        helper = UserAuthenticationStorageHelper(twitch, self.user_scope, storage_path=Path(self.target_channel))
        await helper.bind()

        self.chat = await Chat(twitch)
        self.chat.register_event(ChatEvent.READY, self.__on_ready)
        self.chat.start()

        while self.chat.is_ready() == False:
            await asyncio.sleep(1)

        while self.stop_req == False:
            await asyncio.sleep(0.5)
        self.chat.stop()
        await twitch.close()

    

if __name__ == "__main__":
    USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
    TARGET_CHANNEL = 'artofdestroy'
    sender = TwitchSender(key_file="credential/twitch_key.json", target_channel=TARGET_CHANNEL, user_scope=USER_SCOPE)

    asyncio.run(sender.twitch_async_run())