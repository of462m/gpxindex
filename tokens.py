import re
from gpxpy.gpx import GPX
from enum import IntEnum, auto


class Seasons(IntEnum):
    NONE = auto()
    WINTER = auto()
    SPRING = auto()
    SUMMER = auto()
    AUTUMN = auto()


def tokenize(s: str) -> tuple:
    s = s.lower().replace('ё', 'е')
    res = list()
    season = Seasons.NONE
    pr = (
        'на', 'по', 'из', 'от', 'за', 'до', 'перед', 'без', 'через', 'над', 'про',
        'под', 'для', 'после', 'при', 'между', 'около', 'среди', 'вокруг', 'мимо',
        'возле', 'вдоль', 'спереди', 'слева', 'справа,' 'сзади', 'туда',
        'обратно', 'же', 'этот', 'тот',
    )
    mon = ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
           'янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
           )
    mday = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
            'пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс',
            )

    winter_tokens = ('зима', 'зимой', 'зимний', 'зимняя', 'зимнее', 'зимние',)
    spring_tokens = ('весна', 'весной', 'весенний', 'весенняя', 'весеннее', 'весенние',)
    summer_tokens = ('лето', 'летом', 'летний', 'летняя', 'летнее', 'летние',)
    autumn_tokens = ('осень', 'осенью', 'осенний', 'осенняя', 'осеннее', 'осенние',)

    strava = ('strava', 'by', 'stravatogpx', 'app')

    trash = ('трек', 'http', 'но', 'теперь', 'вся', 'весь', 'не', 'км')

    remove_symbols_queue0 = '\n,;:\'"=()!?[]<>{}|*&^%$#@^|~_+-/\\'

    for symbol in remove_symbols_queue0:
        s = s.replace(symbol, ' ')
        s = re.sub(r'\d{1,4}', r'', s)

    for word in s.lower().split():
        word = re.sub(r'^\d{1,4}', r'', word)
        # word = re.sub(r'ст\.(\w+)', r'старая \1', word)
        # word = re.sub(r'ст\.', r'старая', word)
        word = re.sub(r'^ск\.(\w+)?$', r'скал \1', word)
        # word = re.sub(r'^ск\.', r'скал', word)
        word = re.sub(r'^п\.(\w+)?$', r'пик \1', word)
        # word = re.sub(r'^п\.', r'пик', word)
        word = re.sub(r'^пер\.(\w+)?$', r'перевал \1', word)
        # word = re.sub(r'^пер\.', r'перевал', word)
        word = re.sub(r'^оз\.(\w+)?$', r'озеро \1', word)
        # word = re.sub(r'^оз\.', r'озеро', word)
        word = re.sub(r'^р\.(\w+)?$', r'река \1', word)
        # word = re.sub(r'^р\.', r'река', word)
        word = re.sub(r'^руч\.(\w+)?$', r'ручей \1', word)
        # word = re.sub(r'^руч\.', r'ручей', word)
        word = re.sub(r'^зим\.(\w+)?$', r'зимовье \1', word)
        # word = re.sub(r'^зим\.', r'зимовье', word)
        word = re.sub(r'^м\.(\w+)?$', r'мыс \1', word)
        word = re.sub(r'^бух\.(\w+)?$', r'бухта \1', word)
        word = re.sub(r'^пещ\.(\w+)?$', r'пещера \1', word)
        word = re.sub(r'^ст\.(\w+)?$', r'станция старая \1', word)
        word = re.sub(r'^ур\.(\w+)?$', r'урочище \1', word)
        word = re.sub(r'^о\.(\w+)?$', r'остров озеро \1', word)

        word = word.replace('.', ' ')

        for token in word.split():
            if token in winter_tokens:
                season = Seasons.WINTER
            elif token in spring_tokens:
                season = Seasons.SPRING
            elif token in summer_tokens:
                season = Seasons.SUMMER
            elif token in autumn_tokens:
                season = Seasons.AUTUMN
            elif len(token) > 1 and token not in [*pr, *strava, *mon, *mday, *trash, ]:
                res.append(token)

    return list(set(res)), season


def get_wtokens(gpx: GPX) -> tuple:
    wtokens = list()
    if gpx.name:
        wtokens.append(gpx.name)
    # trk-ов может быть несколько!
    for trk in gpx.tracks:
        if trk.name:
            wtokens.append(trk.name)
        if trk.description:
            if len(trk.description) < 256:
                wtokens.append(trk.description)
    for rte in gpx.routes:
        if rte.name:
            wtokens.append(rte.name)
    return tokenize(' '.join(wtokens))


if __name__ == '__main__':
    tokens, season = tokenize('осенний мунку спрдыг')
    if season.value == Seasons.WINTER:
        print('зима')
    if season.value == Seasons.SPRING:
        print('весна')
    if season.value == Seasons.SUMMER:
        print('лето')
    if season.value == Seasons.AUTUMN:
        print('осень')
