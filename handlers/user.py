from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from DB import DB
from handlers import other


# @dp.message_handler(state=FSMAdmin.course_command)
async def show_course(message: types.Message, state: FSMContext):
    course_data = DB.query("""SELECT * FROM currency WHERE name = %s""", ('CNY',))
    course = course_data[0][2]
    await state.finish()
    await other.start(message, state, 'Текущий курс = ' + course)


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(show_course, lambda message: message.text == "Показать курс", state="*")
