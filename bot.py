from aiogram.utils import executor
from create_bot import dp
from handlers import admin, other, user

other.register_other_handlers(dp)
admin.register_admin_handlers(dp)
user.register_user_handlers(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
