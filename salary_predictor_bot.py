import os

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import parsing
import inference

from bot_database import BotDatabaseHandler


BOT_TOKEN = '...'


bot_database_handler = BotDatabaseHandler('bot_database.db')

bot = Bot(token=os.environ['BOT_TOKEN'])
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    bot_database_handler.add_user(message.from_user.id)
    await message.reply('Привет! Тебе доступны следующие команды:\n'
                        '/salary url - предсказать нижнюю границу заработной платы в BYN для вакансии, доступной по ссылке url с сайта rabota.by,\n'
                        '/help - вывести доступные команды,\n'
                        '/history - вывести историю поиска,\n'
                        '/clear - очистить историю поиска,\n'
                        '/models - вывести доступные модели предсказания заработной платы,\n'
                        '/change_model model_name - поменять модель предсказания заработной платы.')


@dp.message_handler(commands=['help'])
async def get_help(message: types.Message) -> None:
    await message.reply('Бот поддерживает следующие команды:\n'
                        '/salary url - предсказать нижнюю границу заработной платы в BYN для вакансии, доступной по ссылке url с сайта rabota.by,\n'
                        '/help - вывести доступные команды,\n'
                        '/history - вывести историю поиска,\n'
                        '/clear - очистить историю поиска,\n'
                        '/models - вывести доступные модели предсказания заработной платы,\n'
                        '/change_model model_name - поменять модель предсказания заработной платы.')


@dp.message_handler(commands=['history'])
async def get_history(message: types.Message) -> None:
    query_history = bot_database_handler.get_query_history(message.from_user.id)
    if query_history:
        await message.reply('История поиска:\n' + query_history)
    else:
        await message.reply('История поиска пуста.')


@dp.message_handler(commands=['clear'])
async def clear_history(message: types.Message) -> None:
    bot_database_handler.clear_history(message.from_user.id)
    await message.reply('История поиска очищена')


@dp.message_handler(commands=['models'])
async def get_models(message: types.Message) -> None:
    models = bot_database_handler.get_models()
    await message.reply('Доступны следующие модели:\n' + models + '\n'
                        f'В данный момент выбрана модель {bot_database_handler.get_model_name_from_user_id(message.from_user.id)}.')


@dp.message_handler(commands=['change_model'])
async def change_model(message: types.Message) -> None:
    model_name = message.get_args()
    new_model_id = bot_database_handler.get_id_from_model_name(model_name)

    if new_model_id == -1:
        await message.reply('Такой модели нет среди доступных. Чтобы узнать, какие модели доступны, воспользуйся командой /models.')
    else:
        bot_database_handler.set_user_model_id(message.from_user.id, new_model_id)
        await message.reply(f'Модель изменена на {model_name}.')


@dp.message_handler(commands=['salary'])
async def get_salary(message: types.Message) -> None:
    url = message.get_args()
    vacancy_id = parsing.get_vacancy_id_from_url(url)

    model_id = bot_database_handler.get_model_id_from_user_id(message.from_user.id)
    model_info = bot_database_handler.get_model_info_from_id(model_id)
    salary = await inference.get_salary(vacancy_id, model_info)

    await message.reply(f'Нижняя граница заработной платы для данной вакансии составляет {salary} BYN.')
    
    bot_database_handler.add_query_info(user_id=message.from_user.id, vacancy_id=message.text, model_id=model_id, predicted_salary=salary)


if __name__ == '__main__':
    executor.start_polling(dp)
    bot_database_handler.teardown()
