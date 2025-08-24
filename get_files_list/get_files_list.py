#!/usr/bin/env python3

import sys
import argparse
import os
import datetime
import hashlib
import zlib

INITIAL_DEPTH = 1
SLASH = "|"
HASH_METHODS = ['crc32', 'md5', 'crc32', 'sha256', 'sha512', 'sha384', 'sha1']
DEFAULT_HASH_METHOD = HASH_METHODS[0]

MESSAGE_KIND__COMMENT = "c"
MESSAGE_KIND__VERBOSE = "i"
MESSAGE_KIND__DEBUG = "d"
MESSAGE_KIND__WARNING = "w"
MESSAGE_KIND__ERROR = "e"
MESSAGE_KIND__FATAL = "f"
MESSAGE_KIND__QUESTION = "q"
MESSAGE_KIND__RAW = "r"
COMMENT_SYMBOL = "#"

DEBUG_MODE = True
_DEBUG_ARGS = []
#_DEBUG_ARGS = ["scan",  "-o", "/tmp/scan1.txt", "--append", "--size", "/tmp", "/var"]
#_DEBUG_ARGS = ["scan",  "-o", "/tmp/scan1.txt", "--size", "-T", "-H", "--follow-symlinks", "--min-size=1000", "/tmp"]
#_DEBUG_ARGS = ["scan",  "-o", "/tmp/scan1.txt", "--size", "-T", "-H", "--follow-symlinks", "--min-size=1000", "--min-age", "10d", "--min-time=2025.02.01", "/tmp"]

#SKIP_DEFAULT = [
#    ".wine/dosdevices"
#]

def fill_advanced_hash_methods(methods) -> None:
    for x in hashlib.algorithms_available:
        if x not in methods:
            methods.append(x)
fill_advanced_hash_methods(HASH_METHODS)
#print(HASH_METHODS); exit(0)


def get_parser_definiton():
    parser = argparse.ArgumentParser(
        prog = 'get_files_list',
        description = """Выяснение списка изменившихся файлов в ходе выполнения как
1) Составить список файлов до установки или настройки программы (состояние "А");
2) Произвести установку или настройку программы;
3) Составить список файлов (состояние "Б");
4) Сравнить два списка файлов, результаты записать в файл различий;
5) На основе файла различий собрать установочный пакет приводящий систему из состояния "А" в состояние "Б".""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    #parser.add_argument("-p", "--print", default=False, required=False, action='store_true', help='Дублировать на экран (в <stdout>) строки записываемые в файл результата')

    #commands_subparsers = parser.add_subparsers(title='commands', dest='commands')
    subparsers_commands = parser.add_subparsers(help='Справка по командам', dest='command')

    hash_methods_str = ", ".join(HASH_METHODS)
    parser_scan = subparsers_commands.add_parser('scan', help='Сканирование')
    parser_scan.add_argument('-p', '--print', action='store_true', help='Вывод на экран, даже если выполняется вывод в файл (при наличии параметра -o | --output <filename>)')
    parser_scan.add_argument('-o', '--output', help='Файл с результатами сканирования')
    parser_scan.add_argument('-a', '--append', action='store_true', help='Если файл результатов существует - добавить в него вместо создания нового')
    parser_scan.add_argument('-m', '--method', help='Метод вычисления контрольных суммм: ' + hash_methods_str, default=DEFAULT_HASH_METHOD)
    parser_scan.add_argument('-S', '--size', action='store_true', help='Получать размеры файлов')
    parser_scan.add_argument('-T', '--time', action='store_true', help='Получать время модификации файлов')
    parser_scan.add_argument('-H', '--hash', action='store_true', help='Получать контрольные суммы файлов')
    parser_scan.add_argument('--follow-symlinks', action='store_true', help='Для символических ссылок на каталоги переходить в каталог на который указывает ссылка')
    parser_scan.add_argument('--max-depth', type=int, help='Максимальный уровень сканирования. 0 - без ограничений (по умолчанию), 1 - толоько указанные каталоге без подкаталогов, 2 - указанные каталоги и их подкаталоги первого уровня и т.д.', default=0)
    parser_scan.add_argument('--min-size', type=int, help='Минимальный размер файлов отражаемый в результатах поиска')
    parser_scan.add_argument('--max-size', type=int, help='Максимальный размер файлов отражаемый в результатах поиска')
    parser_scan.add_argument('--min-time', help='Файл должен быть изменён после указанной даты в формате "yyyy-mm-dd HH:MM:SS (время можно не указывать)')
    parser_scan.add_argument('--max-time', help='Файл должен быть изменён до указанной даты в формате "yyyy-mm-dd HH:MM:SS (время можно не указывать)')
    parser_scan.add_argument('--min-age', help='Файл должен существовать дольше указанного интервала (примеры: 1year, 3mn, "4 Day" - один год, 3 месяца, 4 дня)')
    parser_scan.add_argument('--max-age', help='Файл должен существовать меньше указанного интервала (примеры: 1year, 3mn, "4 Day" - один год, 3 месяца, 4 дня)')
    parser_scan.add_argument('directory', nargs='+', help='Сканируемый каталог (можно указать несколько через пробел)')

    parser_compare = subparsers_commands.add_parser('compare', help='Сравнение двух результатов сканирования')
    parser_compare.add_argument('-o', '--output', help='Файл с результатами сравнения. Если не указан - вывод в <stdout>')

    return parser


def get_hash__from_hashlib(filename, method, block_size = 2**20):
    result = ""
    if not os.path.isfile(filename):
        return result
    try:
        f = open(filename, "rb")
        while True:
            data = f.read(block_size)
            if not data:
                break
            method.update(data)
        result = method.hexdigest()
    except:
        result = 'Cannot read file "{}"' . format(filename)
    return result


def get_hash__crc32(filename):
    result = ""
    if not os.path.isfile(filename):
        return result
    try:
        file = open(filename, 'rb')
        buf = file.read()
        result = hex(zlib.crc32(buf))
        file.close()
    except:
        result = 'Cannot read file "{}"' . format(filename)
    return result


def get_hash(filename, method):
    result = ""
    if not os.path.isfile(filename):
        return result
    if method == 'crc32':
        # +++ crc32 with zlib +++
        result = get_hash__crc32(filename)
    elif method in hashlib.algorithms_available:
        # +++ алгоритмы из hashlib +++
        BLOCK_SIZE = 2**2        
        method_hashlib = hashlib.new(method)
        result = get_hash__from_hashlib(filename, method_hashlib, BLOCK_SIZE)
    else:
        result = 'unknown method of calculating hash-sum: "{}"' . format(method)
    return result

#print(HASH_METHODS)
#print(get_hash('/tmp/scan1.txt', 'crc32')); exit(0)
#print(get_hash('/tmp/scan1.txt', 'md5')); exit(0)
#print(get_hash('/tmp/scan1.txt', 'sha256')); exit(0)
#print(get_hash('/tmp/scan1.txt', 'sha512')); exit(0)
#print(get_hash('/tmp/scan1.txt', 'md4')); exit(0)
#print(get_hash('/tmp/scan1.txt', 'sha384')); exit(0)
#print(get_hash('/tmp/scan1.txt', 'blake2s')); exit(0)


#s1 = get_link_attr_str("/tmp/varlink"); print(s1); exit(0)
#s1 = get_link_attr_str("/tmp/scan1b.txt"); print(s1); exit(0)

def get_file_attr_str(filename, args):
    result = filename
    
    # +++ размер +++
    if args.size:
        try:
            attr = os.path.getsize(filename)
            if not args.min_size is None and attr < args.min_size:
                return None
            if not args.max_size is None and attr > args.max_size:
                return None
            attr = str(attr)
        except:
            attr = '?'
        result += '\t' + attr

    # +++ время изменения +++
    if args.size:
        try:
            attr_ts = os.path.getmtime(filename)
            #attr = datetime.datetime.fromtimestamp(attr).strftime('%Y-%m-%d %H:%M:%S')
            attr_dt = datetime.datetime.fromtimestamp(attr_ts)
            if not args._skip_before is None and attr_dt < args._skip_before:
                return None
            if not args._skip_after is None and attr_dt > args._skip_before:
                return None
            attr = attr_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            attr = '?'
        result += '\t' + attr

    # +++ контрольная сумма +++
    if args.hash:
        try:
            attr = get_hash(filename, args.method)
        except:
            attr = '?'
        result += '\t' + attr
        
    return result



# --- Дата и время в виде строки (yyyy-mm-dd hh:mm:ss) ---
def get_timestamp(some_date_time = None, date_divider = "-", date_time_divider = " ", time_divider = ":"):
    if some_date_time is None:
        some_date_time = datetime.datetime.now()
    ts_format = "%Y" + date_divider + "%m" + date_divider + "%d" + date_time_divider + "%H" + time_divider + "%M" + time_divider + "%S"
    ts = some_date_time.strftime(ts_format)
    return ts

#print(get_timestamp(None, "-", "T", ":"))
#exit(0)

"""
def build_scan_result_string(kind, path, attr = None):
    result = path
    if kind == 'd':
        result += SLASH
    elif kind =='f':
        if attr['size'] is None:
            result += '\t' + '-'
        else:
            result += '\t' + str(attr['size'])

        if attr['time'] is None:
            result += '\t' + '-'
        else:
            #result += '\t' + get_timestamp(attr['time'])
            result += '\t' + datetime.datetime.fromtimestamp(attr['time']).strftime('%Y-%m-%d %H:%M:%S')

        if attr['hash'] is None:
            result += '\t' + '-'
        else:
            result += '\t' + attr['hash']

    return result
"""

def prepare_message(message:str, kind:str = "") -> str:
    if len(message) == 0:
        #return "" # не указан текст сообщения
        return None # если не указан текст сообщения для пользователя, то ничего и не выводить
    if message[0].islower():
        # перевести первый символ в верхний регистр, если он в нижнем
        ch = message[0]
        ch = ch.upper()
        message = ch + message[1:len(message)]
    punctuation_symbol = "."
    if kind == MESSAGE_KIND__VERBOSE:
        if VERBOSE_MODE:
            message = "INFO. " + message
        else:
            return None
    elif kind == MESSAGE_KIND__WARNING:
        message = "WARNING! " + message
        punctuation_symbol = "!"
    elif kind == MESSAGE_KIND__ERROR:
        message = "ERROR!!! " + message
        punctuation_symbol = "!"
    elif kind == MESSAGE_KIND__FATAL:
        message = "FATAL_ERROR!!! " + message
        punctuation_symbol = "!"
    elif kind == MESSAGE_KIND__DEBUG:
        if DEBUG_MODE:
            message = "Debug: " + message
        else:
            return None
    elif kind == MESSAGE_KIND__QUESTION:
        message = "QUESTION: " + message
        punctuation_symbol = "?"
    elif kind != "":
        message = kind + message
    if message[-1] not in (".", "!", "?"):
        message += punctuation_symbol # если строка не заканчивется символом пунктуации, то поставить соответствующий типу сообщения знак пунктуации
    return message


def print_message(message:str, kind:str = MESSAGE_KIND__RAW, display:bool = True, file_stream:any = None) -> None:
    #if len(message) == 0: убрать, чтобы можно было выводить пустые строки
    #    return
    if kind != "" and kind != MESSAGE_KIND__RAW and kind != MESSAGE_KIND__COMMENT:
        # Если это сообщение для пользователя, внести коррективы в текст (начать с большой буквы, знаки препинания в конце, добавить название типа сообщения)
        message = prepare_message(message, kind)
        if message == None:
            return # не включен режим, при котором выводить сообщения данного типа
    if kind != MESSAGE_KIND__RAW and message[0] != COMMENT_SYMBOL:
        message = COMMENT_SYMBOL + " " + message

    if file_stream != None:
        #message_to_file_stream = message
        #if kind != MESSAGE_KIND__RAW and message[0] != COMMENT_SYMBOL:
        #    # если это сообщение для пользователя и символ комментария не стоит - добавить символ комментария
        #    message_to_file_stream = COMMENT_SYMBOL + " " + message
        #file_stream.write(message_to_file_stream + "\n")
        file_stream.write(message + "\n")
    if kind == MESSAGE_KIND__FATAL:
        raise Exception(message)
    if display:
        print(message)


def do_scan(root_dir, file_stream, args, depth = INITIAL_DEPTH):
    if depth == INITIAL_DEPTH:
        print('begin scan [{}]' . format(root_dir))
    try:
        items = os.listdir(root_dir)
    except:
        print_message("Cannot read [{}]" . format(root_dir), MESSAGE_KIND__ERROR, True, file_stream)
        return

    # +++ обработка файлов root_dir +++
    for one_item in items:
        path = os.path.join(root_dir, one_item)
        if os.path.islink(path):
            line = path + '\t' + '=>' + '\t' + os.path.realpath(path)
            print_message(line, MESSAGE_KIND__RAW, args.print, file_stream)
        elif  os.path.isfile(path):
            line = get_file_attr_str(path, args)
            if not line is None:
                print_message(line, MESSAGE_KIND__RAW, args.print, file_stream)

    # +++ обработка каталогов root_dir +++
    for one_item in items:
        path = os.path.join(root_dir, one_item)
        if os.path.isdir(path):
            if os.path.islink(path) and not args.follow_symlinks:
                # ссылка на каталог и не включен переход по ссылкам - пропустить
                continue
            path += SLASH
            print_message(path, MESSAGE_KIND__RAW, args.print, file_stream)
            if args.max_depth == 0 or depth < args.max_depth:
                do_scan(path, file_stream, args, depth+1)


def get_output(filename, append, command):
    if filename is None:
        return None
    if filename == '':
        return None
    if append:
        mode = 'at'
    else:
        mode = 'wt'
    f = open(filename, mode)
    msg = '\t'
    msg += '---'
    msg  += ' [' + get_timestamp() + ']'
    msg += ' Begin ' + command
    msg += ' ---'
    print_message(msg, MESSAGE_KIND__COMMENT, False, f)
    return f

def close_output(f, command):
    msg = '\t'
    msg += '---'
    msg  += ' [' + get_timestamp() + ']'
    msg += ' Complete ' + command
    msg += ' ---'
    print_message(msg, MESSAGE_KIND__COMMENT, False, f)


def age_one_measure(age, measure):
    if age.lower().endswith(measure):
        value_str = age[0:len(age)-len(measure)]
        if value_str == '':
            value_int = 1
        else:
            value_int = int(value_str)


# Из строки вида <dd.mm.yyyy[ hh:mm:ss]> или <yyyy.mm.dd[ hh:mm:ss]> получить дату; если недопустимый формат - вернуть None
def str_to_date(s):
    year = None
    month = None
    day = None
    hour = 0
    minute = 0
    second = 0
    result = None
    if len(s) < 10:
        return None # недостаточно символов, чтобы уместилась дата
    # dd.mm.yyyy    yyyy.mm.dd
    # 0123456789    0123456789
    if s[0].isdigit() and s[1].isdigit() and not(s[2].isdigit()) and s[3].isdigit() and s[4].isdigit() and not(s[5].isdigit()) and s[6].isdigit() and s[7].isdigit() and s[8].isdigit() and s[9].isdigit():
        day = int(s[0:2])
        month = int(s[3:5])
        year = int(s[6:10])
    elif s[0].isdigit() and s[1].isdigit() and s[2].isdigit() and s[3].isdigit() and not(s[4].isdigit()) and s[5].isdigit() and s[6].isdigit() and not(s[7].isdigit()) and s[8].isdigit() and s[9].isdigit():
    #elif s[0].isdigit() and s[1].isdigit() and s[2].isdigit()  and s[3].isdigit() and not(s[4].isdigit()):
        year = int(s[0:4])
        month = int(s[5:7])
        day = int(s[8:10])
    else:
        # строка не совпадает ни с одним из форматов: dd.mm.yyyy    yyyy.mm.dd
        return None
    
    #dd.mm.yyyy hh:mm:ss
    #0123456789012345678
    if len(s) >= 13 and s[11].isdigit() and s[12].isdigit():
        hour = int(s[11:13])
    if len(s) >= 16 and s[14].isdigit() and s[15].isdigit():
        minute = int(s[14:16])
    if len(s) >= 19 and s[17].isdigit() and s[18].isdigit():
        second = int(s[17:19])
    try:
        result = datetime.datetime(year, month, day, hour, minute, second)
    except:
        return None
    return result
    
#d1 = str_to_date("31.12.2012 08:11:59"); print(d1); exit(0)
#d1 = str_to_date("2012-12-31 09:11:59"); print(d1); exit(0)
#d1 = str_to_date("2012-02-31 09:11:59"); print(d1); exit(0)


# ----- В объекте типа datetime.datetime изменить месяц -----
def inc_months(sourcedate, months):
    import calendar
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.datetime(year, month, day, sourcedate.hour, sourcedate.minute, sourcedate.second, sourcedate.microsecond)

# ----- Изменение даты заданое строкой вида "-10year",  "5 Hours", "-86400" (количество секунд в сутках) -----
def inc_date(timedelta_str, dt0 = datetime.datetime.now()):
    timedelta_measure = ''
    i = len(timedelta_str) - 1
    while i >= 0 and timedelta_str[i] not in '0123456789':
        timedelta_measure = timedelta_str[i] + timedelta_measure
        i -= 1
    timedelta_value_str = timedelta_str[0:len(timedelta_str)-len(timedelta_measure)]
    timedelta_value_str = timedelta_value_str.strip()
    if timedelta_value_str == '':
        timedelta_value_int = 1
    else:
        timedelta_value_int = int(timedelta_value_str)

    timedelta_measure = timedelta_measure.lower()
    timedelta_measure = timedelta_measure.strip()
    if timedelta_measure == '':
        timedelta_measure = 's'

    if timedelta_measure in ['y', 'year', 'years']:
        year = dt0.year
        month = dt0.month
        day = dt0.day
        hour = dt0.hour
        minute = dt0.minute
        second = dt0.second
        microsecond = dt0.microsecond
        year += timedelta_value_int
        result = datetime.datetime(year, month, day, hour, minute, second, microsecond)
    elif timedelta_measure in ['mn', 'month', 'months']:
        result = inc_months(dt0, timedelta_value_int)
    elif timedelta_measure in ['d', 'day', 'days']:
        result = dt0 + datetime.timedelta(days = timedelta_value_int)
    elif timedelta_measure in ['h', 'hour', 'hours']:
        result = dt0 + datetime.timedelta(hours = timedelta_value_int)
    elif timedelta_measure in ['m', 'mins', 'minute', 'minutes']:
        result = dt0 + datetime.timedelta(minutes = timedelta_value_int)
    elif timedelta_measure in ['s', 'sec', 'second', 'seconds']:
        result = dt0 + datetime.timedelta(seconds = timedelta_value_int)
    elif timedelta_measure in ['w', 'week', 'weeks']:
        result = dt0 + datetime.timedelta(weeks = timedelta_value_int)
    else:
        result = dt0
    return result

#print(inc_date('-51 Week')); exit(0)
#print(inc_date('100 years')); exit(0)
#print(inc_date('-3 mn')); exit(0)
#print(inc_date('-365 day')); exit(0)
#print(inc_date('48 hour')); exit(0)
#print(inc_date('1440 mins')); exit(0)
#print(inc_date('-60 seconds')); exit(0)
#print(inc_date(' 60 ')); exit(0)

    
def prepare_arguments(args):
    if (args.print == False or args.print is None) and args.output is None:
        args.print = True
    args._skip_before = None
    args._skip_after = None
    if not args.min_age is None:
        args._skip_after = inc_date('-' + args.min_age)
    if not args.max_age is None:
        args._skip_before = inc_date('-' + args.max_age)
    if not args.min_time is None:
        d = str_to_date(args.min_time)
        if not d is None:
            args._skip_before = d
    if not args.max_time is None:
        d = str_to_date(args.max_time)
        if not d is None:
            args._skip_after = d
    return args

if __name__ == "__main__":
    #f1();exit(0)
    #parser = f2a()
    if os.path.isfile('/etc/passwd'):
        SLASH = '/'
    else:
        SLASH = '\\'
    parser = get_parser_definiton()
    #print(parser)
    if len(_DEBUG_ARGS) > 0:
        # использовать отладочные параметры
        args = parser.parse_args(_DEBUG_ARGS)
    else:
        # использовать реальные параметры командной строки
        if len(sys.argv) == 1:
            # параметров в командной стрке не задано - вывести справку и выйти
            parser.print_help()
            exit(0)
        args = parser.parse_args()

    args = prepare_arguments(args)
    #print("args:", args); exit(0)

    if args.command == 'help':
        print('help...')
    elif args.command == 'scan':
        print('scan...')
        #print("output:", args.output)
        #print("dirs[]:", args.directory)
        f = get_output(args.output, args.append, args.command)
        print('output:', f)
        for d in args.directory:
            do_scan(d, f, args)
        close_output(f, args.command)
    elif args.command == 'compare':
        print('compare...')
    exit(0)

    parser = get_parser_definiton()
    #args = parser.parse_args()
    parser.print_help()
