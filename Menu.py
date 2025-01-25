from aiogram import types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import requests
from bs4 import BeautifulSoup

# Поиск новых игр в Steam
def get_new_steam_games():
    url = "https://store.steampowered.com/search/?sort_by=Released_DESC"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    games = []
    for item in soup.select(".search_result_row"):
        title = item.select_one(".title").text.strip()
        link = item["href"]
        games.append({"title": title, "link": link})

    return games

# Поиск видео на YouTube
def search_youtube_videos(query, max_results=5):
    YOUTUBE_API_KEY = "AIzaSyBDkS60u01OGSRkgHaJdkubD62dfp__uso"
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "type": "video"
    }
    response = requests.get(url, params=params)
    return response.json()

# Обработчик кнопки "Новые игры в Steam"
async def handle_new_steam_games(callback: types.CallbackQuery):
    games = get_new_steam_games()
    response = "Новые игры в Steam:\n"
    for game in games[:5]:  # Показать первые 5 игр
        response += f"- {game['title']}: {game['link']}\n"
    await callback.message.answer(response)
    await callback.answer()

# Обработчик кнопки "Стримы и видео"
async def handle_streams_and_videos(callback: types.CallbackQuery):
    await callback.message.answer("Введи название игры для поиска видео:")
    await callback.answer()

# Обработчик текстового сообщения для поиска видео
async def handle_video_search(message: types.Message):
    query = message.text
    videos = search_youtube_videos(query)
    response = f"Результаты поиска для '{query}':\n"
    for video in videos["items"]:
        title = video["snippet"]["title"]
        video_id = video["id"]["videoId"]
        response += f"- {title}: https://www.youtube.com/watch?v={video_id}\n"
    await message.answer(response)

# Функция для регистрации обработчиков
def register_menu(dp):
    dp.callback_query.register(handle_new_steam_games, F.data == "new_steam_games")
    dp.callback_query.register(handle_streams_and_videos, F.data == "streams")
    dp.message.register(handle_video_search, F.text)