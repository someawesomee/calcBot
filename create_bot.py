from aiogram import Bot
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from Config import Config

global_course = 0
storage = MemoryStorage()
config = Config()
token = config.get('Bot', 'token')
bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)
