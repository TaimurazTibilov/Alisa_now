# coding: utf-8
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

import calendar
import datetime

import util_func as func
# Импортируем модули для работы с JSON и логами.
import json
import logging

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Хранилище данных о сессиях.
sessionStorage = {}

buffer = {}

# id дедлайнов
id = 1

loc_id = 0


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
            "title": "Нет",
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
            'stage': 0,
            'substage': 0,
            'user_id': user_id,
            'deadlines': []
        }
        hello = 'Привет! Я твой ассистент дедлайнов. Здесь ты можешь ' \
                'отслеживать текущие дедлайны. \n Приступим?'
        res['response']['text'] = hello
        res['response']['buttons'] = stage0_buttons
        return

    if sessionStorage[user_id]['substage'] == 0:
        if handle_help(user_id, req, res):
            return

    if sessionStorage[user_id]['substage'] == 0:
        if handle_exit(user_id, req, res):
            return

    if sessionStorage[user_id]['stage'] == 0:
        stage0(user_id, req, res)
    elif sessionStorage[user_id]['stage'] == 1:
        if 0 < sessionStorage[user_id]['substage'] < 5:
            substages(user_id, req, res)
            return
        stage1(user_id, req, res)
    elif sessionStorage[user_id]['stage'] == 3:
        if 0 < sessionStorage[user_id]['substage']:
            edit_stages(user_id, req, res)
            return
        stage3(user_id, req, res)


def handle_exit(user_id, req, res):
    if req['request']['original_utterance'].lower() in [
        'не хочу',
        'нет',
        'не',
        'не сегодня',
        'выход',
        'завершить',
        'закройя'
    ]:
        res['response']['text'] = 'Приходи еще! Хорошего дня!'
        res['response']['end_session'] = True
        return True
    return False


def handle_help(user_id, req, res):
    if req['request']['original_utterance'].lower() in [
        'помощь',
        'что ты умеешь?',
        'что ты умеешь',
    ]:
        res['response'][
            'text'] = 'Я могу запомнить твои дедлайны и напомнит тебе о них в будущем по почте.' \
                      ' Пока я только умею сохранять их, но в будущем я стану умнее :)'
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
        'назад'
    ]:
        # Пользователь согласился, идем на стадию 1.
        sessionStorage[user_id]['stage'] = 1
        res['response']['text'] = 'Чем могу вам помочь?'
        res['response']['buttons'] = stage1_buttons
        return

    res['response']['text'] = 'Я вас не поняла'
    res['response']['buttons'] = stage0_buttons


stage1_buttons = \
    [
        {
            "title": "Текущие дедлайны",
            "hide": True
        },
        {
            "title": "Добавить дедлайн",
            "hide": True
        },
        {
            "title": "Смотреть ближайшие",
            "hide": True
        },
        {
            "title": "Выход",
            "hide": True
        },
    ]

back_button = [
    {
        'title': 'Назад',
        'hide': True
    }
]


# Основной функционал
def stage1(user_id, req, res):
    # Показывает ближайшие дедлайны
    if req['request']['original_utterance'].lower() in [
        'ближайшие',
        'дедлайны',
        'ближайшие дедлайны',
        'покажи ближайшие дедлайны',
        'смотреть ближайшие дедлайны',
        'смотреть ближайшие'
    ]:
        num = len(sessionStorage[user_id]['deadlines'])
        if num == 0:
            res['response']['text'] = 'У вас еще нет дедлайнов. Но их можно добавить.'
        else:
            result = f'Вот ближайшие дедлайны: \n'
            deadlines = list(sessionStorage[user_id]['deadlines'])
            for i in range(min(num, 3)):
                result += func.return_deadline(deadlines[i])
            res['response']['text'] = result
        sessionStorage[user_id]['stage'] = 0
        res['response']['buttons'] = back_button
        return

    # Управление всеми дедлайнами
    elif req['request']['original_utterance'].lower() in [
        'покажи все дедлайны',
        'текущие дедлайны',
        'все дедлайны',
    ]:
        num = len(sessionStorage[user_id]['deadlines'])
        res['response']['text'] = f'У вас запланировано {num} дедлайнов. \n'
        for dl in sessionStorage[user_id]['deadlines']:
            res['response']['text'] += func.return_deadline(dl)
        res['response']['buttons'] = manage_buttons
        sessionStorage[user_id]['stage'] = 3
        return

    # Добавление дедлайна
    elif req['request']['original_utterance'].lower() in [
        'добавить',
        'добавить дедлайн',
        'новый дедлайн',
        'создать дедлайн',
        'создать новый дедлайн',
        'добавить новый дедлайн'
    ]:
        buffer[id] = {
            'id': id
        }
        res['response']['text'] = f'Отлично! Начнем с названия. Какое название добавим?'
        sessionStorage[user_id]['substage'] = 1
        return

    res['response']['text'] = 'Я вас не поняла'


stage2_buttons = \
    [
        {
            "title": "На сегодня",
            "hide": True
        },
        {
            "title": "На завтра",
            "hide": True
        },
        {
            "title": "На неделю",
            "hide": True
        }
    ]

manage_buttons = [
    {
        "title": "Изменить",
        "hide": True
    },
    {
        "title": "Удалить",
        "hide": True
    },
    {
        "title": "Назад",
        "hide": True
    }
]


# def stage2(user_id, req, res):
#     date = try_parse_date(req['request']['nlu']['entities'])
#     if date is not None:
#         deadlines = []
#         for dl in sessionStorage[user_id]['deadlines']:
#             if dl['date'] <= date:
#                 deadlines.append(dl)
#         if len(deadlines) == 0:
#             res['response']['text'] = 'У вас еще нет дедлайнов, которые вы могли бы закрыть'
#             sessionStorage[user_id]['stage'] = 0
#             res['response']['buttons'] = back_button
#             return
#         result = 'Вот все дедлайны, которые вам нужно сделать до ' + str(date) + '\n'
#         for dl in deadlines:
#             result += func.return_deadline(dl)
#         sessionStorage[user_id]['stage'] = 3
#         res['response']['text'] = result + '\nХотите что-то изменить или удалить?'
#         res['response']['buttons'] = manage_buttons
#         return
#
#     res['response']['text'] = 'Я вас не поняла. На какую дату хотите увидеть расписание?'
#     res['response']['buttons'] = stage2_buttons
#     return


def stage3(user_id, req, res):
    if req['request']['original_utterance'].lower() in [
        'не',
        'нет',
        'нет спасибо',
        'не хочу',
        'назад',
    ]:
        sessionStorage[user_id]['stage'] = 1
        res['response']['text'] = 'Отлично! Чем еще я могу вам помочь?'
        res['response']['buttons'] = stage1_buttons

    elif req['request']['original_utterance'].lower() in [
        'удали',
        'удалить',
        'убери',
        'убрать',
    ]:
        sessionStorage[user_id]['substage'] = 5
        res['response']['text'] = 'Какой дедлайн вы хотели бы удалить?'

    elif req['request']['original_utterance'].lower() in [
        'измени',
        'поменяй',
        'отредактируй',
        'изменить',
    ]:
        sessionStorage[user_id]['substage'] = 6
        res['response']['text'] = 'Какой дедлайн вы хотели бы изменить?'

    elif req['request']['original_utterance'].lower() in [
        'не',
        'нет',
        'нет спасибо',
        'не хочу',
        'назад',
    ]:
        sessionStorage[user_id]['stage'] = 1
        res['response']['text'] = 'Отлично! Чем еще я могу вам помочь?'
        res['response']['buttons'] = stage1_buttons
    else:
        res['response']['text'] = 'Что вы хотите сделать?'


edit_buttons = [
    {
        "title": "Имя",
        "hide": True
    },
    {
        "title": "Дату",
        "hide": True
    },
    {
        "title": "Приоритет",
        "hide": True
    }
]


def parse_int(entities):
    data = None
    for i in entities:
        if i["type"] == "YANDEX.NUMBER":
            data = i["value"]
    return data


def edit_stages(user_id, req, res):
    global loc_id
    if sessionStorage[user_id]['substage'] == 5:
        loc_id = parse_int(req['request']['nlu']['entities'])
        if loc_id is not None:
            deldl = sessionStorage[user_id]['deadlines'][loc_id - 1]
            if deldl is None:
                res['response']['text'] = 'Дедлайна с таким номером не существует.'
                return
            sessionStorage[user_id]['deadlines'].remove(deldl)
            sessionStorage[user_id]['substage'] = 0
            sessionStorage[user_id]['stage'] = 1
            res['response']['text'] = 'Дедлайн успешно удален. Чем могу вам помочь еще?'
            res['response']['buttons'] = stage1_buttons
            return
        else:
            res['response']['text'] = 'Я вас не понимаю. Попробуйте еще.'
            return
    elif sessionStorage[user_id]['substage'] == 6:
        loc_id = parse_int(req['request']['nlu']['entities'])
        if loc_id is not None:
            deldl = sessionStorage[user_id]['deadlines'][loc_id - 1]
            if deldl is None:
                res['response']['text'] = 'Дедлайна с таким номером не существует.'
                return
            res['response']['text'] = 'Что вы хотели бы изменить?'
            sessionStorage[user_id]['substage'] = 7
            res['response']['buttons'] = edit_buttons
            return
        res['response']['text'] = 'Я вас не понимаю. Попробуйте еще.'
        return

    elif sessionStorage[user_id]['substage'] == 7:
        if req['request']['original_utterance'].lower() in [
            'имя',
            'название'
        ]:
            sessionStorage[user_id]['substage'] = 8
            res['response']['text'] = 'Введите новое имя'
            return

        elif req['request']['original_utterance'].lower() in [
            'дату',
            'время'
        ]:
            sessionStorage[user_id]['substage'] = 9
            res['response']['text'] = 'Скажите новую дату'
            res['response']['buttons'] = [
                {
                    'title': 'Сегодня',
                    'hide': True
                },
                {
                    'title': 'Завтра',
                    'hide': True
                }
            ]
            return

        elif req['request']['original_utterance'].lower() in [
            'приоритет',
            'значимость'
        ]:
            sessionStorage[user_id]['substage'] = 10
            res['response']['text'] = 'Назовите или выберите новый приоритет'
            res['response']['buttons'] = priotity_buttons
            return
        else:
            res['response']['text'] = 'Я вас не понимаю. Попробуйте еще.'
            return

    elif sessionStorage[user_id]['substage'] == 8:
        data = sessionStorage[user_id]['deadlines'][loc_id - 1]
        data['name'] = req['request']['original_utterance']
        sessionStorage[user_id]['substage'] = 0
        sessionStorage[user_id]['stage'] = 1

        res['response']['text'] = 'Отлично! Чем еще я могу вам помочь?'
        res['response']['buttons'] = stage1_buttons

    elif sessionStorage[user_id]['substage'] == 9:
        data = sessionStorage[user_id]['deadlines'][loc_id - 1]
        date = try_parse_date(req['request']['nlu']['entities'])
        if date is not None:
            data['date'] = date
            sessionStorage[user_id]['substage'] = 0
            sessionStorage[user_id]['stage'] = 1

            res['response']['text'] = 'Отлично! Чем еще я могу вам помочь?'
            res['response']['buttons'] = stage1_buttons
        else:
            res['response']['text'] = 'Я вас не понимаю'
            res['response']['buttons'] = [
                {
                    'title': 'Сегодня',
                    'hide': True
                },
                {
                    'title': 'Завтра',
                    'hide': True
                }
            ]

    elif sessionStorage[user_id]['substage'] == 10:
        data = sessionStorage[user_id]['deadlines'][loc_id - 1]
        if req['request']['original_utterance'].lower() in [
            'низкий',
            'маленький'
        ]:
            data['priority'] = 'Низкий'
        elif req['request']['original_utterance'].lower() in [
            'средний',
            'обычный'
        ]:
            data['priority'] = 'Средний'
        elif req['request']['original_utterance'].lower() in [
            'важный',
            'большой',
            'высокий'
        ]:
            data['priority'] = 'Высокий'
        else:
            res['response']['text'] = 'Я вас не понимаю'
            res['response']['buttons'] = priotity_buttons
            return
        sessionStorage[user_id]['substage'] = 0
        sessionStorage[user_id]['stage'] = 1

        res['response']['text'] = 'Отлично! Чем еще я могу вам помочь?'
        res['response']['buttons'] = stage1_buttons
        return


priotity_buttons = [
    {
        'title': 'Низкий',
        'hide': True
    },
    {
        'title': 'Средний',
        'hide': True
    },
    {
        'title': 'Высокий',
        'hide': True
    },
]

choice_buttons = [
    {
        'title': 'Да',
        'hide': True
    },
    {
        'title': 'Нет',
        'hide': True
    },
]


def substages(user_id, req, res):
    global id
    if sessionStorage[user_id]['substage'] == 1:
        buffer[id]['name'] = req['request']['original_utterance']
        sessionStorage[user_id]['substage'] = 2
        res['response']['text'] = 'Замечательно! Теперь укажите, на какой день назначен дедлайн?'
        res['response']['buttons'] = [
            {
                'title': 'Сегодня',
                'hide': True
            },
            {
                'title': 'Завтра',
                'hide': True
            }
        ]
        return

    elif sessionStorage[user_id]['substage'] == 2:
        date = try_parse_date(req['request']['nlu']['entities'])
        if date is not None:
            sessionStorage[user_id]['substage'] = 3
            buffer[id]['date'] = date
            res['response']['text'] = 'Отлично! Осталось только выбрать приоритет задачи.'
            res['response']['buttons'] = priotity_buttons
            return

    elif sessionStorage[user_id]['substage'] == 3:
        if req['request']['original_utterance'].lower() in [
            'низкий',
            'маленький'
        ]:
            buffer[id]['priority'] = 'Низкий'
        elif req['request']['original_utterance'].lower() in [
            'средний',
            'обычный'
        ]:
            buffer[id]['priority'] = 'Средний'
        elif req['request']['original_utterance'].lower() in [
            'важный',
            'большой',
            'высокий'
        ]:
            buffer[id]['priority'] = 'Высокий'
        else:
            res['response']['text'] = 'Я вас не понимаю'
            res['response']['buttons'] = priotity_buttons
            return
        sessionStorage[user_id]['substage'] = 4
        res['response']['text'] = 'Прекрасно! Все ли верно вы заполнили?\n'
        res['response']['text'] += func.return_deadline(buffer[id])
        res['response']['buttons'] = choice_buttons
        return

    elif sessionStorage[user_id]['substage'] == 4:
        if req['request']['original_utterance'].lower() in [
            'да',
            'все ок',
            'ок',
            'класс',
            'ага',
        ]:
            sessionStorage[user_id]['substage'] = 0
            sessionStorage[user_id]['stage'] = 1
            id += 1
            sessionStorage[user_id]['deadlines'].append(buffer[id - 1])

            res['response']['text'] = 'Отлично! Чем еще я могу вам помочь?'
            res['response']['buttons'] = stage1_buttons
        elif req['request']['original_utterance'].lower() in [
            'не',
            'нет',
            'плохо',
            'не ок',
            'измени',
        ]:
            sessionStorage[user_id]['substage'] = 1
            res['response']['text'] = 'Давайте создадим сначала. Какое название у дедлайна?'
        else:
            res['responce']['text'] = 'Я вас не понимаю'
    else:
        res['response']['text'] = 'Произошла ошибка. Попробуем сначала. Чем могу вам помочь?'
        sessionStorage[user_id]['stage'] = 1
        res['response']['buttons'] = stage1_buttons
        return


def try_parse_date(entities):
    date = None
    for i in entities:
        if i["type"] == "YANDEX.DATETIME":
            v = i["value"]
            d = datetime.datetime.now()
            is_relative = False
            day = d.day
            if "day" in v:
                if "day_is_relative" in v and v["day_is_relative"]:
                    is_relative = True
                    d += datetime.timedelta(days=v["day"])
                    day += v["day"]
                else:
                    day = v["day"]
            if day < 10:
                day = f"0{day}"
            month = d.month
            if "month" in v:
                if "month_is_relative" in v and v["month_is_relative"]:
                    is_relative = True
                    d = add_months(d, v["month"])
                    month += v["month"]
                else:
                    month = v["month"]
            if month < 10:
                month = f"0{month}"
            year = d.year
            if "year" in v:
                if "year_is_relative" in v and v["year_is_relative"]:
                    is_relative = True
                    d = add_years(d, v["year"])
                    year += v["year"]
                else:
                    year = v["year"]
            if is_relative:
                month = d.month
                if d.month < 10:
                    month = f"0{month}"
                day = d.day
                if d.day < 10:
                    day = f"0{day}"
                date = f"{d.year}.{month}.{day}"
            else:
                date = f"{year}.{month}.{day}"
    return date


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


from calendar import isleap


def add_years(d, years):
    new_year = d.year + years
    try:
        return d.replace(year=new_year)
    except ValueError:
        if (d.month == 2 and d.day == 29 and  # leap day
                isleap(d.year) and not isleap(new_year)):
            return d.replace(year=new_year, day=28)
        raise
