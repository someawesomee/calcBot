import math

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from . import admin
from DB import DB


class FSMCalc(StatesGroup):
    calc_2 = State()
    calc_3 = State()
    calc_4 = State()


# @dp.message_handler(commands=['start'])
async def start(message, state: FSMContext, text='Выберите нужное действие'):
    if isinstance(message, types.Message):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if admin.check_admin(message.from_user.id):
            buttons = [
                "Показать курс",
                "Рассчитать",
                "Управление категориями",
                "Админка"
            ]
        else:
            buttons = [
                "Показать курс",
                "Рассчитать",
                "Список"
            ]
        keyboard.add(*buttons)
        await state.finish()
        await message.answer(text, reply_markup=keyboard)
    elif isinstance(message, types.CallbackQuery):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if admin.check_admin(message.from_user.id):
            buttons = [
                "Показать курс",
                "Рассчитать",
                "Управление категориями",
                "Админка"
            ]
        else:
            buttons = [
                "Показать курс",
                "Рассчитать",
                "Список"
            ]
        keyboard.add(*buttons)
        await state.finish()
        await message.message.answer(text, reply_markup=keyboard)


# @dp.message_handler(commands=['help'])
async def show_help(message: types.Message):
    await message.reply("Привет!\nНапиши мне что-нибудь!")


async def calc_1(message: types.Message, state: FSMContext):
    buttons = admin.cat_buttons_list(True)
    if len(buttons) != 0:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await FSMCalc.calc_2.set()
        await message.answer('Выберите категорию', reply_markup=keyboard)
    else:
        await admin.menu(message, state, 'Категорий с подкатегориями нет')


async def calc_2(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    cat_id = call.data
    buttons = admin.subcat_buttons_list(cat_id)
    if len(buttons) != 0:
        async with state.proxy() as data:
            data['cat_id'] = cat_id
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await FSMCalc.calc_3.set()
        await call.message.answer('Выберите подкатегорию', reply_markup=keyboard)
    else:
        await admin.menu(call, state, 'Подкатегории не найдены')


async def calc_3(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    subcat_id = call.data
    async with state.proxy() as data:
        cat_id = data['cat_id']
    select_result = DB.query(
        """SELECT * FROM subcategories WHERE id = %s AND parent_cat_id = %s""",
        (subcat_id, cat_id)
    )
    if len(select_result) != 0:
        async with state.proxy() as data:
            data['charge_type'] = select_result[0][3]
            data['subcat_name'] = select_result[0][1]
            data['charge'] = select_result[0][4]
        await FSMCalc.calc_4.set()
        await call.message.answer('Введите сумму в юанях (только целые числа)')
    else:
        await admin.menu(call, state, 'Подкатегория не найдена')


async def calc_4(message: types.Message, state: FSMContext):
    input_integer = message.text
    if input_integer.isdigit():
        course_data = DB.query("""SELECT * FROM currency WHERE name = %s""", ('CNY',))
        if len(course_data) != 0:
            course = course_data[0][2]
            async with state.proxy() as data:
                charge_type = data['charge_type']
                charge = data['charge']
                subcat_name = data['subcat_name']
            calc_result = 0
            no_charge_price = 0
            match charge_type:
                case 1:
                    charge_type = 'Статическая'
                    no_charge_price = float(input_integer) * float(course)
                    calc_result = no_charge_price + float(charge)
                case 2:
                    charge_type = 'Динамическая'
                    no_charge_price = float(input_integer) * float(course)
                    result_charge = 0
                    # декодим формулу, получаем словарь
                    charge_pieces = admin.formula_decode(charge)
                    # сортируем по возрастанию
                    charge_pieces = dict(sorted(charge_pieces.items()))
                    # перебираем, смотрим словия на установку наценки
                    # (итоговая цена больше или равна минимальному порогу для установленной наценки)
                    for charge_data in charge_pieces:
                        if int(input_integer) >= int(charge_data):
                            result_charge = charge_pieces[charge_data]
                        else:
                            break
                    calc_result = no_charge_price + float(result_charge)
            if admin.check_admin(message.from_user.id):
                await start(
                    message,
                    state,
                    'Подкатегория = "' + subcat_name + '"\n' +
                    'Тип наценки (' + str(charge_type) + ')\n\n' +
                    'Наценка (' + str(charge) + ')\n' +
                    'Стоимость без наценки (' + str(round(no_charge_price)) + 'р.)\n' +
                    'Курс = ' + course + '\n\n' +
                    'Итоговая стоимость = ' + str(round(calc_result)) + 'р.\n' +
                    'Округленная = ' + str(math.ceil(calc_result / 500) * 500) + 'р.')
            else:
                await start(
                    message,
                    state,
                    'Подкатегория = "' + subcat_name + '"\n' +
                    'Итоговая стоимость = ' + str(math.ceil(calc_result / 500) * 500) + 'р.')
        else:
            await message.answer('Не удалось получить курс, попробуйте еще раз')
    else:
        await message.answer('Не удалось получить число, попробуйте еще раз')


def register_other_handlers(dp: Dispatcher):
    dp.register_message_handler(start, lambda message: message.text == "Главное меню", state="*")
    dp.register_message_handler(start, commands=["start"], state="*")
    dp.register_message_handler(help, commands=["help"], state="*")
    dp.register_message_handler(calc_1, lambda message: message.text == "Рассчитать", state="*")
    dp.register_callback_query_handler(calc_2, state=FSMCalc.calc_2)
    dp.register_callback_query_handler(calc_3, state=FSMCalc.calc_3)
    dp.register_message_handler(calc_4, state=FSMCalc.calc_4)
