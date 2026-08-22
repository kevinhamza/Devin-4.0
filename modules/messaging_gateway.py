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
