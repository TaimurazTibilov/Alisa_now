# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import json
import logging

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Хранилище данных о сессиях.
sessionStorage = {}


# Задаем параметры приложения Flask.
@app.route("/", methods=['POST'])
def main():
    # Функция получает тело запроса и возвращает ответ.
    logging.info('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


stage0_buttons = \
            [
                {
                    "title": "Давай",
                    "hide": True
                },
                {
                    "title": "Не сегодня",
                    "hide": True
                }
            ]

# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.

        sessionStorage[user_id] = {
            'stage': 0
        }
        hello = 'Привет! Я могу рассказать о твоем расписании занятий в Высшей Школе Экономики. \n Но сначала нам нужно познакомиться.'
        res['response']['text'] = hello
        res['response']['buttons'] = stage0_buttons
        return

    if handle_exit(user_id, req, res):
        return

    if sessionStorage[user_id]['stage'] == 0:
        stage0(user_id, req, res)
    elif sessionStorage[user_id]['stage'] == 1:
        stage1(user_id, req, res)
    elif sessionStorage[user_id]['stage'] == 2:
        stage2(user_id, req, res)
    elif sessionStorage[user_id]['stage'] == 3:
        stage3(user_id, req, res)


def handle_exit(user_id, req, res):
    if req['request']['original_utterance'].lower() in [
        'не хочу',
        'нет',
        'не',
        'не сегодня',
    ]:
        res['response']['text'] = 'Жаль. Приходи еще.'
        res['response']['end_session'] = True
        return True
    return False


def stage0(user_id, req, res):
    # Обрабатываем ответ пользователя.
    if req['request']['original_utterance'].lower() in [
        'давай',
        'ладно',
        'ок',
        'хорошо',
        'ага',
    ]:
        # Пользователь согласился, идем на стадию 1.
        sessionStorage[user_id] = {
            'stage': 1
        }
        res['response']['text'] = 'Для начала мне нужен твой E-mail, заканчивающийся на @edu.hse.ru'
        return

    # Если нет, то убеждаем его купить слона!
    res['response']['text'] = 'Я вас не поняла'
    res['response']['buttons'] = stage0_buttons
    return


stage1_buttons = \
            [
                {
                    "title": "Сегодня",
                    "hide": True
                },
                {
                    "title": "Завтра",
                    "hide": True
                },
                {
                    "title": "На неделю",
                    "hide": True
                }
            ]


def stage1(user_id, req, res):
    email = req['request']['original_utterance'].lower()

    if str(email).endswith("@edu.hse.ru"):  # todo check email is valid
        sessionStorage[user_id] = {
            'stage': 2,
            'email': str(email)
        }
        res['response']['text'] = f"Ваш email: {email}. На какие даты показать расписание?"
        res['response']['buttons'] = stage1_buttons
        return
    res['response']['text'] = 'Я вас не поняла. Чтобы показать расписание мне нужен твой E-mail, заканчивающийся на @edu.hse.ru'


stage2_buttons = \
            [
                {
                    "title": "А сегодня",
                    "hide": True
                },
                {
                    "title": "А завтра",
                    "hide": True
                },
                {
                    "title": "А на неделю",
                    "hide": True
                }
            ]


def stage2(user_id, req, res):
    if req['request']['original_utterance'].lower() in [
        'сегодня',
        'а сегодня',
    ]:
        res['response']['text'] = 'Поздравляю. Пар на сегодня нет.'  # todo go to API
        res['response']['buttons'] = stage2_buttons[-2:]
        return
    if req['request']['original_utterance'].lower() in [
        'завтра',
        'а завтра',
    ]:
        res['response']['text'] = 'Поздравляю. Пар на завтра нет.'  # todo go to API
        res['response']['buttons'] = [stage2_buttons[0], stage2_buttons[2]]
        return
    if req['request']['original_utterance'].lower() in [
        'на неделю',
        'а на неделю',
    ]:
        res['response']['text'] = 'Поздравляю. Пар на неделю нет.'  # todo go to API
        res['response']['buttons'] = stage2_buttons[:2]
        return

    res['response']['text'] = 'Я вас не поняла. На какие даты показать расписание?'
    res['response']['buttons'] = stage1_buttons
    return


def stage3(user_id, req, res):
    pass