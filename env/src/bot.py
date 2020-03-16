import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from json_parser import Handle_test

logging.basicConfig(level=logging.INFO)

API_TOKEN = '1036464931:AAHCyvEDv3ahK3rIvBAOxiPiP9t66ap973o'

bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# States
class Form(StatesGroup):
    question = State()
    answered = State()

# Markups
markup_inline = types.InlineKeyboardMarkup(row_width=4)
markup_inline.row(types.InlineKeyboardButton(text='1', callback_data='1'),
           types.InlineKeyboardButton(text='2', callback_data='2'),
           types.InlineKeyboardButton(text='3', callback_data='3'),
           types.InlineKeyboardButton(text='4', callback_data='4'))

markup_final = types.InlineKeyboardMarkup(row_width=1)
markup_final.row(types.InlineKeyboardButton(text="Показать результаты", callback_data='completed'))

def get_question(lst):
    question = lst[0]
    lst.pop(0)
    return question

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, "Вам предлагается пройти тест")
    async with state.proxy() as data:
        data[message.chat.id] = Handle_test("test.json").values_lst
        data['question'] = get_question(data[message.chat.id])
        data['answered'] = []
        await bot.send_message(message.chat.id, data['question'], reply_markup=markup_inline)
    await Form.question.set()

@dp.callback_query_handler(lambda callback_query: 'completed' not in callback_query.data, state=Form.question)
async def callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_reply_markup(callback_query.from_user.id, callback_query.message.message_id, reply_markup=None)
    await bot.answer_callback_query(callback_query.id, text="Вы ответили на вопрос")
    try:
        async with state.proxy() as data:
            data['answered'].append(int(callback_query.data))
            data['question'] = get_question(data[callback_query.message.chat.id])
            await bot.send_message(callback_query.from_user.id, data['question'], reply_markup=markup_inline)
            await Form.question.set()
    except IndexError:
        await bot.send_message(callback_query.from_user.id, "Тест завершен", reply_markup=markup_final)
        await Form.next()

@dp.callback_query_handler(lambda callback_query: 'completed' in callback_query.data, state=Form.answered)
async def display_result(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data: 
        result = sum(data['answered'])
        if result <= 21:
            await bot.send_message(callback_query.from_user.id, "Вы набрали {} баллов. Это соответствует незначительному уровню тревоги".format(result))
        elif result >= 22 and result <= 35:
            await bot.send_message(callback_query.from_user.id, "Вы набрали {} баллов. Это говорит о средней выраженности тревоги".format(result))
        elif result > 35:
            await bot.send_message(callback_query.from_user.id, "Вы набрали {} баллов. Это сильная тревога. Не пора ли к врачу?".format(result))
    await state.finish()

@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())
 
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
