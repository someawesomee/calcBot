from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from DB import DB
from . import other


class FSMCategory(StatesGroup):
    cat_menu = State()

    charge_1 = State()
    charge_2 = State()
    charge_3 = State()
    charge_4 = State()
    charge_5 = State()

    delete_menu_1 = State()
    delete_menu_2 = State()
    cat_delete_2 = State()
    subcat_delete_2 = State()
    subcat_delete_3 = State()

    create_menu_1 = State()
    create_menu_2 = State()
    cat_add_2 = State()
    subcat_add_2 = State()
    subcat_add_3 = State()

    admin_menu = State()

    admin_add_1 = State()
    admin_add_2 = State()
    admin_add_3 = State()

    admin_delete_1 = State()
    admin_delete_2 = State()

    admin_list_1 = State()

    currency_set_2 = State()


async def cat_list(message: types.Message, state: FSMContext):
    message_text = ''
    categories_list = DB.query("""SELECT * FROM categories""")
    if len(categories_list) != 0:
        for category in categories_list:
            subcategories_list = DB.query("""SELECT * FROM subcategories WHERE parent_cat_id = %s """, (category[0],))
            message_text += '"' + str(category[1]) + '"\n'
            if len(subcategories_list) != 0:
                for subcategory in subcategories_list:
                    message_text += '\t\t\t - "' + subcategory[1] + '"\n'
            else:
                message_text += '\t\t\t - Подкатегории не найдены\n'
        await menu(message, state, message_text)
    else:
        await menu(message, state, 'Категории не найдены')


async def charge_1(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        buttons = cat_buttons_list(True)
        if len(buttons) != 0:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await FSMCategory.charge_2.set()
            await message.answer('Выберите категорию', reply_markup=keyboard)
        else:
            await menu(message, state, 'Категории с подкатегориями не найдены')
    else:
        await menu(message, state, 'Нет доступа')


async def charge_2(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if check_admin(call.from_user.id):
        cat_id = call.data
        select_result = DB.query(
            """SELECT * FROM categories WHERE id = %s""",
            (cat_id,)
        )
        if len(select_result) != 0:
            async with state.proxy() as data:
                data['cat_id'] = select_result[0][0]
                data['cat_name'] = select_result[0][1]
            buttons = subcat_buttons_list(cat_id)
            if len(buttons) != 0:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(*buttons)
                await call.message.delete()
                await FSMCategory.charge_3.set()
                await call.message.answer(
                    'Выберите подкатегорию, в которой хотите изменить наценку',
                    reply_markup=keyboard
                )
            else:
                await call.message.delete()
                await menu(call, state, 'В этой категории не подкатегорий')
        else:
            await call.message.answer('Категория не найдена')
    else:
        await call.message.delete()
        await menu(call, state, 'Нет доступа')


async def charge_3(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if check_admin(call.from_user.id):
        subcat_id = call.data
        async with state.proxy() as data:
            cat_id = data['cat_id']
            data['subcat_id'] = subcat_id
        subcategory = DB.query("""SELECT * FROM subcategories WHERE id = %s AND parent_cat_id = %s""",
                               (subcat_id, cat_id))
        if len(subcategory) != 0:
            buttons = [
                types.InlineKeyboardButton(text='Фиксированная', callback_data='1'),
                types.InlineKeyboardButton(text='Динамическая', callback_data='2')
            ]
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await call.message.delete()
            await FSMCategory.charge_4.set()
            await call.message.answer('Укажите тип наценки', reply_markup=keyboard)
        else:
            await FSMCategory.charge_4.set()
            await call.message.answer('Подкатегория не найдена')
    else:
        await call.message.delete()
        await menu(call, state, 'Нет доступа')


async def charge_4(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if check_admin(call.from_user.id):
        charge_type = call.data
        async with state.proxy() as data:
            subcat_id = data['subcat_id']
        subcategory = DB.query("""SELECT * FROM subcategories WHERE id = %s""", (subcat_id,))
        if len(subcategory) != 0:
            match charge_type:
                case '1':
                    await call.message.delete()
                    await FSMCategory.charge_5.set()
                    await call.message.answer('Укажите фиксированную наценку в валюте')
                    async with state.proxy() as data:
                        data['charge_type'] = charge_type
                case '2':
                    await call.message.delete()
                    await FSMCategory.charge_5.set()
                    await call.message.answer(
                        'Укажите формулу для расчета в формате (минимальный порог цены в валюте = наценка,...)'
                        '\nНапример: 100=543,600=2173 ('
                        'при цене от 100 до 600 наценка = 543, '
                        'от 600 = 2173, '
                        'при цене до 100 наценка = 0)'
                    )
                    async with state.proxy() as data:
                        data['charge_type'] = charge_type
        else:
            await call.message.answer('Подкатегория не найдена')
    else:
        await call.message.delete()
        await menu(call, state, 'Нет доступа')


async def charge_5(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        charge = message.text
        async with state.proxy() as data:
            charge_type = data['charge_type']
            subcat_id = data['subcat_id']
            cat_id = data['cat_id']
        match charge_type:
            case '1':
                if charge.isdigit():
                    DB.query(
                        """UPDATE subcategories SET charge_type = %s, charge = %s """ +
                        """WHERE id = %s AND parent_cat_id = %s""",
                        (charge_type, charge, subcat_id, cat_id)
                    )
                    await menu(message, state, 'Наценка установлена')
                else:
                    await message.answer('Фиксированная наценка должна быть целым числом')
            case '2':
                formula = formula_decode(charge)
                if len(formula):
                    DB.query(
                        """UPDATE subcategories SET charge_type = %s, charge = %s """ +
                        """WHERE id = %s AND parent_cat_id = %s""",
                        (charge_type, charge, subcat_id, cat_id)
                    )
                    await menu(message, state, 'Наценка установлена')
                else:
                    await message.answer('Формула не корректна')
    else:
        await menu(message, state, 'Нет доступа')


async def delete_menu_1(message: types.Message):
    if check_admin(message.from_user.id):
        buttons = []
        buttons.append(types.InlineKeyboardButton(text='Категорию', callback_data='1'))
        buttons.append(types.InlineKeyboardButton(text='Подкатегорию', callback_data='2'))
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await FSMCategory.delete_menu_2.set()
        await message.answer('Что удалить?', reply_markup=keyboard)


async def delete_menu_2(call: types.CallbackQuery):
    await call.answer()
    await call.message.delete()
    if check_admin(call.from_user.id):
        method = call.data
        match method:
            case '1':
                buttons = cat_buttons_list()
                if len(buttons) != 0:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    keyboard.add(*buttons)
                    await FSMCategory.cat_delete_2.set()
                    await call.message.answer('Выберите категорию', reply_markup=keyboard)
                else:
                    await call.message.answer('Удалять нечего')
            case '2':
                buttons = cat_buttons_list(True)
                if len(buttons) != 0:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    keyboard.add(*buttons)
                    await FSMCategory.subcat_delete_2.set()
                    await call.message.answer(
                        'Выберите категорию из которой хотите удалить подкатегорию',
                        reply_markup=keyboard
                    )
                else:
                    await call.message.answer('Категорий с подкатегориями не найдено', )


async def cat_delete_2(call: types.CallbackQuery):
    await call.answer()
    if check_admin(call.from_user.id):
        cat_id = call.data
        categories = DB.query(
            """SELECT * FROM categories WHERE id = %s""", (cat_id,)
        )
        if len(categories) != 0:
            DB.query(
                """DELETE FROM categories WHERE id = %s""", (cat_id,)
            )
            DB.query("""DELETE FROM subcategories WHERE parent_cat_id = %s""", (cat_id,))
            await FSMCategory.cat_menu.set()
            await call.message.delete()
            await call.message.answer('Категория "' + categories[0][1] + '" удалена вместе с ее подкатегориями')
        else:
            await call.message.answer('Категория не найдена')
    else:
        await call.message.delete()


async def subcat_delete_2(call: types.CallbackQuery):
    await call.answer()
    if check_admin(call.from_user.id):
        cat_id = call.data
        buttons = subcat_buttons_list(cat_id)
        if len(buttons) != 0:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await call.message.delete()
            await FSMCategory.subcat_delete_3.set()
            await call.message.answer(
                'Выберите подкатегорию',
                reply_markup=keyboard
            )
        else:
            await call.message.answer('Подкатегории не найдены')
    else:
        await call.message.delete()


async def subcat_delete_3(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    if check_admin(call.from_user.id):
        subcat_id = call.data
        DB.query("""DELETE FROM subcategories WHERE id = %s""", (subcat_id,))
        await menu(call, state, 'Подкатегория удалена')
    else:
        await menu(call, state, 'Нет доступа')


async def create_menu_1(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        buttons = []
        buttons.append(types.InlineKeyboardButton(text='Категорию', callback_data='1'))
        buttons.append(types.InlineKeyboardButton(text='Подкатегорию', callback_data='2'))
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await FSMCategory.create_menu_2.set()
        await message.answer('Что добавить?', reply_markup=keyboard)
    else:
        await menu(message, state, 'Нет доступа')


async def create_menu_2(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.delete()
    if check_admin(call.from_user.id):
        method = call.data
        match method:
            case '1':
                await FSMCategory.cat_add_2.set()
                await call.message.answer('Введите имя категории')
            case '2':
                buttons = cat_buttons_list()
                if len(buttons) != 0:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    keyboard.add(*buttons)
                    await FSMCategory.subcat_add_2.set()
                    await call.message.answer(
                        'Выберите категорию, в которую будет добавляться подкатегория',
                        reply_markup=keyboard
                    )
                else:
                    await call.message.answer('Категории не найдены')
    else:
        await menu(call, state, 'Нет доступа')


async def cat_add_2(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        name = message.text.strip()
        select_result = DB.query(
            """SELECT * FROM categories WHERE name = %s""",
            (name,)
        )
        if len(select_result) == 0:
            DB.query(
                """INSERT INTO categories (id, name) VALUES (%s, %s)""",
                (None, name,)
            )
            await FSMCategory.cat_menu.set()
            await message.answer('Категория "' + name + '" создана')
        else:
            await message.answer('Категория с таким именем уже есть')
    else:
        await menu(message, state, 'Нет доступа')


async def subcat_add_2(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    if check_admin(call.from_user.id):
        category_id = call.data
        select_category = DB.query("""SELECT * FROM categories WHERE id = %s""", (category_id,))
        if len(select_category) != 0:
            message_text = 'Введите название подкатегории\n'
            subcategories_list = DB.query("""SELECT * FROM subcategories WHERE parent_cat_id = %s""", (category_id,))
            if len(subcategories_list) != 0:
                message_text += 'Текущий список подкатегорий в этой категории:\n'
                for subcategory in subcategories_list:
                    message_text += '"' + subcategory[1] + '"\n'
            async with state.proxy() as data:
                data['cat_name'] = select_category[0][1]
                data['cat_id'] = category_id
            await call.message.delete()
            await FSMCategory.subcat_add_3.set()
            await call.message.answer(message_text)
        else:
            await call.message.answer('Категория не найдена')
    else:
        await call.message.delete()
        await menu(
            call.message,
            state,
            'Нет доступа'
        )


async def subcat_add_3(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        async with state.proxy() as data:
            category_id = data['cat_id']
            category_name = data['cat_name']
        subcategory_name = message.text.strip()
        subcategory = DB.query(
            """SELECT * FROM subcategories WHERE name =%s AND parent_cat_id = %s""",
            (subcategory_name, category_id,)
        )
        if len(subcategory) == 0:
            DB.query(
                """INSERT INTO subcategories (id, name, parent_cat_id, charge_type, charge )""" +
                """ VALUES (%s,%s, %s, %s, %s)""",
                (None, subcategory_name, category_id, 1, '0')
            )
            await menu(
                message,
                state,
                'Подкатегория "' + subcategory_name +
                '" в категории "' + category_name + '" создана'
            )
        else:
            await message.answer('Подкатегория с таким именем уже есть')


async def cat_menu(message, text='Доступные функции с категориями'):
    if isinstance(message, types.Message):
        if check_admin(message.from_user.id):
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                "Список",
                "Изменить",
                "Удалить",
                "Добавить",
                "Главное меню"
            ]
            keyboard.add(*buttons)
            await FSMCategory.cat_menu.set()
            await message.answer(text, reply_markup=keyboard)
    elif isinstance(message, types.CallbackQuery):
        if check_admin(message.from_user.id):
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                "Список",
                "Изменить",
                "Удалить",
                "Добавить",
                "Главное меню"
            ]
            keyboard.add(*buttons)
            await FSMCategory.cat_menu.set()
            await message.message.answer(text, reply_markup=keyboard)


async def menu(message, state: FSMContext, text, type='menu'):
    match type:
        case 'menu':
            if isinstance(message, types.Message):
                if check_admin(message.from_user.id):
                    await cat_menu(message, text)
                else:
                    await other.start(message, state, text)
            elif isinstance(message, types.CallbackQuery):
                if check_admin(message.from_user.id):
                    await cat_menu(message, text)
                else:
                    await other.start(message, state, text)
        case 'admin':
            if isinstance(message, types.Message):
                if check_admin(message.from_user.id):
                    await admin_menu(message, text)
                else:
                    await other.start(message, state, text)
            elif isinstance(message, types.CallbackQuery):
                if check_admin(message.from_user.id):
                    await admin_menu(message, text)
                else:
                    await other.start(message, state, text)


async def admin(message):
    await admin_menu(message, 'Админка')


async def admin_menu(message, text):
    if isinstance(message, types.Message):
        if check_admin(message.from_user.id):
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                "Список",
                "Удалить",
                "Добавить",
                "Курс",
                "Главное меню"
            ]
            keyboard.add(*buttons)
            await FSMCategory.admin_menu.set()
            await message.answer(text, reply_markup=keyboard)
    elif isinstance(message, types.CallbackQuery):
        if check_admin(message.from_user.id):
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = [
                "Список",
                "Удалить",
                "Добавить",
                "Курс",
                "Главное меню"
            ]
            keyboard.add(*buttons)
            await FSMCategory.admin_menu.set()
            await message.message.answer(text, reply_markup=keyboard)


async def admin_list_1(message: types.Message):
    if check_admin(message.from_user.id):
        admins = DB.query("""SELECT * FROM admins WHERE is_admin = %s""", (1,))
        if len(admins) != 0:
            message_text = ''
            for admin in admins:
                message_text += '"' + admin[2] + '"\n'
            await message.answer(message_text)
        else:
            await message.answer('Админов нет')


async def admin_delete_1(message: types.Message):
    if check_admin(message.from_user.id):
        buttons = []
        admins_list = DB.query(
            """SELECT * FROM admins WHERE id != %s""",
            (message.from_user.id,)
        )
        if len(admins_list) != 0:
            for admin_data in admins_list:
                buttons.append(types.InlineKeyboardButton(
                    text='"' + admin_data[2] + '"', callback_data=admin_data[0])
                )
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await FSMCategory.admin_delete_2.set()
            await message.answer('Кого удалить?', reply_markup=keyboard)
        else:
            await message.answer('Админов кроме вас нет')


async def admin_delete_2(call: types.CallbackQuery):
    await call.answer()
    await call.message.delete()
    if check_admin(call.from_user.id):
        admin_id = call.data
        admin_data = DB.query("""SELECT * FROM admins WHERE id = %s""", (admin_id,))
        if len(admin_data) != 0:
            DB.query("""DELETE FROM admins WHERE id = %s""", (admin_id,))
            await FSMCategory.admin_menu.set()
            await call.message.answer('Админ удален')
        else:
            await call.message.answer('Админ не найден')


async def admin_add_1(message: types.Message):
    if check_admin(message.from_user.id):
        await FSMCategory.admin_add_2.set()
        await message.answer("Введите id пользователя в телеграме")


async def admin_add_2(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        new_admin_id = message.text
        if new_admin_id.isdigit():
            admins_list = DB.query("""SELECT * FROM admins WHERE id = %s""", (new_admin_id,))
            if len(admins_list) == 0:
                async with state.proxy() as data:
                    data['admin_id'] = new_admin_id
                await FSMCategory.admin_add_3.set()
                await message.answer("Введите псендоним админа")
            else:
                await message.answer('Админ с таким id уже есть (псевдоним - "' + admins_list[0][2] + '")')
        else:
            await message.answer("Id пользователя должен быть целым числом")


async def admin_add_3(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        admin_alias = message.text
        async with state.proxy() as data:
            new_admin_id = data['admin_id']
        DB.query("""INSERT INTO admins (id, is_admin,alias) VALUES (%s, %s, %s)""", (new_admin_id, 1, admin_alias))
        await FSMCategory.admin_menu.set()
        await message.answer("Админ добавлен")


def check_admin(tg_user_id):
    result = DB.query("""SELECT * FROM admins WHERE id = %s AND is_admin = %s""", (tg_user_id, 1))
    if len(result) != 0:
        result = True
    else:
        result = False
    return result


async def currency_set_1(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        currency_data = DB.query("""SELECT * FROM currency WHERE name = %s""", ('CNY',))
        await FSMCategory.currency_set_2.set()
        await message.answer(
            'Текущий курс = ' + str(currency_data[0][2]) +
            '\nВведите новый курс\nДля нецелого числа разделитель точка (пример - 23.16)'
        )


async def currency_set_2(message: types.Message, state: FSMContext):
    if check_admin(message.from_user.id):
        new_value = message.text
        if float(new_value) and float(new_value) != 0.0:
            if float(new_value) < 0.0:
                new_value = float(new_value) + (float(new_value) * -2)
            else:
                new_value = float(new_value)
            DB.query("""UPDATE currency SET value = %s WHERE name = %s""", (str(new_value), 'CNY'))
            await FSMCategory.admin_menu.set()
            await message.answer('Курс обновлен')
        else:
            await message.answer('Значение некорректно')


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(
        cat_list,
        lambda message: message.text == "Список",
        state=[None, FSMCategory.cat_menu]
    )

    dp.register_message_handler(cat_menu, lambda message: message.text == "Управление категориями", state=None)

    dp.register_message_handler(delete_menu_1, lambda message: message.text == "Удалить", state=FSMCategory.cat_menu)
    dp.register_callback_query_handler(delete_menu_2, state=FSMCategory.delete_menu_2)
    dp.register_callback_query_handler(cat_delete_2, state=FSMCategory.cat_delete_2)
    dp.register_callback_query_handler(subcat_delete_2, state=FSMCategory.subcat_delete_2)
    dp.register_callback_query_handler(subcat_delete_3, state=FSMCategory.subcat_delete_3)

    dp.register_message_handler(create_menu_1, lambda message: message.text == "Добавить", state=FSMCategory.cat_menu)
    dp.register_callback_query_handler(create_menu_2, state=FSMCategory.create_menu_2)
    dp.register_message_handler(cat_add_2, state=FSMCategory.cat_add_2)
    dp.register_callback_query_handler(subcat_add_2, state=FSMCategory.subcat_add_2)
    dp.register_message_handler(subcat_add_3, state=FSMCategory.subcat_add_3)

    dp.register_message_handler(charge_1, lambda message: message.text == "Изменить", state=FSMCategory.cat_menu)
    dp.register_callback_query_handler(charge_2, state=FSMCategory.charge_2)
    dp.register_callback_query_handler(charge_3, state=FSMCategory.charge_3)
    dp.register_callback_query_handler(charge_4, state=FSMCategory.charge_4)
    dp.register_message_handler(charge_5, state=FSMCategory.charge_5)

    dp.register_message_handler(admin, lambda message: message.text == "Админка", state=None)
    dp.register_message_handler(admin_list_1, lambda message: message.text == "Список", state=FSMCategory.admin_menu)
    dp.register_message_handler(admin_delete_1, lambda message: message.text == "Удалить", state=FSMCategory.admin_menu)
    dp.register_callback_query_handler(admin_delete_2, state=FSMCategory.admin_delete_2)
    dp.register_message_handler(admin_add_1, lambda message: message.text == "Добавить", state=FSMCategory.admin_menu)
    dp.register_message_handler(admin_add_2, state=FSMCategory.admin_add_2)
    dp.register_message_handler(admin_add_3, state=FSMCategory.admin_add_3)

    dp.register_message_handler(currency_set_1, lambda message: message.text == "Курс", state=FSMCategory.admin_menu)
    dp.register_message_handler(currency_set_2, state=FSMCategory.currency_set_2)


def cat_buttons_list(join_subcategories=False):
    buttons = []

    if join_subcategories:
        select_result = DB.query(
            """SELECT * FROM categories AS cats """ +
            """INNER JOIN subcategories AS scats on cats.id = scats.parent_cat_id GROUP BY cats.id"""
        )
    else:
        select_result = DB.query("""SELECT * FROM categories""")
    if len(select_result) != 0:
        for category_data in select_result:
            buttons.append(types.InlineKeyboardButton(
                text=category_data[1], callback_data=category_data[0])
            )
    return buttons


def subcat_buttons_list(cat_id):
    buttons = []
    select_result = DB.query("""SELECT * FROM subcategories WHERE parent_cat_id = %s""", (cat_id,))
    if len(select_result) != 0:
        for subcategory_data in select_result:
            buttons.append(types.InlineKeyboardButton(
                text=subcategory_data[1], callback_data=subcategory_data[0])
            )
    return buttons


def formula_decode(formula):
    result = {}
    formula_blocks = formula.split(',')
    for formula in formula_blocks:
        formula_pieces = formula.split('=')
        formula_condition = formula_pieces[0].strip()
        formula_value = formula_pieces[1].strip()
        if formula_value.isdigit() and formula_condition.isdigit():
            result[int(formula_condition)] = int(formula_value)
    return result
