# Devin/modules/messaging_gateway.py
# Purpose: A multi-channel messaging gateway to allow Devin to communicate
#          via various platforms like Telegram, Discord, and Slack.
#          Ported from OpenClaw features into Python.

import logging
import abc
from typing import Dict, Any, List, Optional, Callable
import threading

logger = logging.getLogger("MessagingGateway")

class MessagingChannel(abc.ABC):
    """Abstract base class for a messaging channel."""
    @abc.abstractmethod
    def send_message(self, recipient_id: str, text: str):
        pass

    @abc.abstractmethod
    def start_listening(self, on_message_received: Callable[[str, str, str], None]):
        """
        Starts listening for incoming messages.
        on_message_received(channel_name, sender_id, text)
        """
        pass

class TelegramChannel(MessagingChannel):
    """Telegram implementation using python-telegram-bot."""
    def __init__(self, token: str):
        self.token = token
        self.bot = None
        try:
            from telegram import Bot
            from telegram.ext import Application, MessageHandler, filters
            self.Bot = Bot
            self.Application = Application
            self.MessageHandler = MessageHandler
            self.filters = filters
            logger.info("Telegram dependencies loaded.")
        except ImportError:
            logger.error("python-telegram-bot not installed. Telegram channel will not work.")
            self.Bot = None

    def send_message(self, recipient_id: str, text: str):
        if not self.Bot: return
        import asyncio
        async def _send():
            bot = self.Bot(token=self.token)
            await bot.send_message(chat_id=recipient_id, text=text)
        asyncio.run(_send())

    def start_listening(self, on_message_received: Callable[[str, str, str], None]):
        if not self.Application: return
        
        async def _handler(update, context):
            sender_id = str(update.effective_chat.id)
            text = update.message.text
            on_message_received("Telegram", sender_id, text)

        def _run():
            application = self.Application.builder().token(self.token).build()
            application.add_handler(self.MessageHandler(self.filters.TEXT & (~self.filters.COMMAND), _handler))
            logger.info("Telegram bot started listening...")
            application.run_polling()

        threading.Thread(target=_run, daemon=True).start()

class DiscordChannel(MessagingChannel):
    """Discord implementation using discord.py, matching openclaw's discord extension pattern."""
    def __init__(self, token: str):
        self.token = token
        self.client = None
        try:
            import discord
            self.discord = discord
            logger.info("Discord dependencies loaded.")
        except ImportError:
            logger.error("discord.py not installed. Discord channel will not work.")
            self.discord = None

    def send_message(self, recipient_id: str, text: str):
        if not self.discord or not self.client:
            return
        import asyncio
        channel = self.client.get_channel(int(recipient_id))
        if channel:
            asyncio.run_coroutine_threadsafe(channel.send(text), self.client.loop)

    def start_listening(self, on_message_received: Callable[[str, str, str], None]):
        if not self.discord:
            return

        intents = self.discord.Intents.default()
        intents.message_content = True
        self.client = self.discord.Client(intents=intents)

        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            on_message_received("Discord", str(message.channel.id), message.content)

        def _run():
            logger.info("Discord bot started listening...")
            self.client.run(self.token)

        threading.Thread(target=_run, daemon=True).start()

class SlackChannel(MessagingChannel):
    """Slack implementation using slack-bolt's Socket Mode (no public URL needed)."""
    def __init__(self, bot_token: str, app_token: str):
        self.bot_token = bot_token
        self.app_token = app_token
        self.app = None
        try:
            from slack_bolt import App
            from slack_bolt.adapter.socket_mode import SocketModeHandler
            self.App = App
            self.SocketModeHandler = SocketModeHandler
            logger.info("Slack dependencies loaded.")
        except ImportError:
            logger.error("slack-bolt not installed. Slack channel will not work.")
            self.App = None

    def send_message(self, recipient_id: str, text: str):
        if not self.app:
            return
        self.app.client.chat_postMessage(channel=recipient_id, text=text)

    def start_listening(self, on_message_received: Callable[[str, str, str], None]):
        if not self.App:
            return

        self.app = self.App(token=self.bot_token)

        @self.app.event("message")
        def _handler(event, say):
            if event.get("subtype") == "bot_message":
                return
            on_message_received("Slack", event.get("channel", ""), event.get("text", ""))

        def _run():
            logger.info("Slack bot started listening (Socket Mode)...")
            self.SocketModeHandler(self.app, self.app_token).start()

        threading.Thread(target=_run, daemon=True).start()

class MessagingGateway:
    """The central gateway for managing multiple messaging channels."""
    def __init__(self):
        self.channels: Dict[str, MessagingChannel] = {}
        self.message_callbacks: List[Callable[[str, str, str], None]] = []

    def register_channel(self, name: str, channel: MessagingChannel):
        self.channels[name] = channel
        channel.start_listening(self._on_message_received)
        logger.info(f"Registered messaging channel: {name}")

    def _on_message_received(self, channel_name: str, sender_id: str, text: str):
        logger.info(f"Message received from {channel_name} ({sender_id}): {text}")
        for callback in self.message_callbacks:
            callback(channel_name, sender_id, text)

    def add_callback(self, callback: Callable[[str, str, str], None]):
        self.message_callbacks.append(callback)

    def send_message(self, channel_name: str, recipient_id: str, text: str):
        if channel_name in self.channels:
            self.channels[channel_name].send_message(recipient_id, text)
        else:
            logger.error(f"Channel '{channel_name}' not found.")

# --- Integration with Devin Core ---
# This would be used in main.py or a dedicated agent interaction module.
