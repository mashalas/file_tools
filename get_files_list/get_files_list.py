#!/usr/bin/env python3

import sys
import argparse
import os
import datetime
import hashlib
import zlib
import fnmatch
#import re

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
#_DEBUG_ARGS = [""]

# убрать миллисекунды после конвертирования даты в строку: datetime.datetime.utcnow().strftime('%F %T.%f')[:-3]
#print( datetime.datetime.now().strftime('%F %T.%f')[:-3] ); exit(0) - не работает

#SKIP_DEFAULT = [
#    ".wine/dosdevices"
#]

DEFAULT_SKIP = [
    # --- Linux ---
    "/proc", 
    "/sys", 
    "/mnt", 
    "/media", 
    "/run", 
    "/var/run", 
    "/root/.local/share/mc", 
    "/dev/fd", 
    "/dev/core", 
    "/var/lib/lxcfs/proc", 
    "/var/lib/lxcfs/cgroup", 
    "/var/lib/lxcfs/sys/devices/system/cpu/online", 
    "/var/lib/systemd/timesync/clock",
    "/etc/mtab",
    "/var/log/journal",

    # --- Midnight Commander (mc) ---
    "/root/.cache/mc/Tree",
    "/root/.config/mc/ini",
    
    # --- apt install (debian) ---
    "/etc/ld.so.cache",
    "/var/cache/apt/pkgcache.bin",
    "/var/cache/ldconfig/aux-cache",
    "/var/cache/man/index.db",
    "/var/lib/apt/extended_states",
    "/var/lib/dpkg/lock",
    "/var/lib/dpkg/status",
    "/var/lib/dpkg/status-old",
    "/var/lib/dpkg/triggers/File"
    "/var/lib/dpkg/triggers/Lock",
    "/var/log/dpkg.log",
    "/var/log/apt/eipp.log.xz",
    "/var/log/apt/history.log",
    "/var/log/apt/term.log",

    # --- apt-get update (debian-12.1) ---
    "/root/.lesshst",
    "/var/cache/apt/srcpkgcache.bin",
    "/var/lib/apt/lists",

    # --- dnf install (rosa) ---
    "/var/cache/dnf/expired_repos.json",
    "/var/cache/dnf/packages.db",
    "/var/cache/dnf/tempfiles.json",
    "/var/lib/dnf/history.sqlite",
    "/var/lib/dnf/history.sqlite-shm",
    "/var/lib/dnf/history.sqlite-wal",
    "/var/lib/rpm/rpmdb.sqlite",
    "/var/lib/rpm/rpmdb.sqlite-shm",
    "/var/lib/rpm/rpmdb.sqlite-wal",
    "/var/log/dnf.librepo.log",
    "/var/log/dnf.log",
    "/var/log/dnf.rpm.log",
    "/var/log/hawkey.log",

    # --- Windows ---
    "pagefile.sys", 
    "swapfile.sys", 
    "DumpStack.log.tmp",
    "NTUSER.DAT", 

    "UsrClass.dat",
    "UsrClass.dat.LOG1",
    "ntuser.dat.LOG1",
    "catdb",
    "edb",
    
    "ntuser.dat.LOG2",
    "DataStore.edb",	# C:\Windows\SoftwaeDistribution\DataStore\
    "MEMORY.DMP",	    # C:\Windows\
    "INDEX.BTR",	    # C:\Windows\System32\wbem\Repository\
    "OBJECTS.DATA"	    # C:\Windows\System32\wbem\Repository\
]


def fill_advanced_hash_methods(methods) -> None:
    for x in hashlib.algorithms_available:
        if x not in methods:
            methods.append(x)
fill_advanced_hash_methods(HASH_METHODS)
#print(HASH_METHODS); exit(0)



def get_arg_parser_definiton():
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
    parser_scan.add_argument('--skip', nargs='*', action="extend", help='Игнорировать файл или каталог соответствующий маске')
    parser_scan.add_argument('--skip-from', nargs='*', action="extend", help='Маски игнорируемых файлов или каталогов прочитать из файла. Каждая строка файла содержит одну маску. Комментарий - #')
    parser_scan.add_argument('directory', nargs='+', help='Сканируемый каталог (можно указать несколько через пробел)')

    parser_compare = subparsers_commands.add_parser('compare', help='Сравнение двух результатов сканирования')
    parser_compare.add_argument('-o', '--output', help='Файл с результатами сравнения. Если не указан - вывод в <stdout>')

    parser_compare = subparsers_commands.add_parser('build', help='Сравнение двух результатов сканирования')
    parser_compare.add_argument('-i', '--input', help='Файл с результатами сравнения. Если не указан - последний файл в текущем каталоге')
    parser_compare.add_argument('-o', '--output', help='Файл с результатами сравнения. Если не указан - создать подкаталог build в текущем каталоге')

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


#---------------- Удалить комментарий начнающийся с символа comment_symbol -------------
def remove_comment(s:str, comment_sequence:str = "#") -> str:
    p = s.find(comment_sequence)
    if p >= 0:
        s = s[0:p]
    return s

#print(remove_comment("str//oka", "//")); exit(0)
#print(remove_comment("str # oka", "#")); exit(0)

# --- Прочитать строки файла в массив ---
def file_to_array(
        filename:str,                           # имя читаемого файла
        comment_sequence:str = "#",             # начало комментария, начисная с которого удалять до конца строки
        strip_spaces_at_begins:bool = False,    # удалять пробельные символы в начале строк
        strip_spaces_at_ends:bool = False,      # удалять пробельные символы в конце строк
        skip_empty_lines:bool = True,           # пропускать пустые строки
        begin_after_sequence:str = "",          # начать после того как встретится эта последовательность символов
        begin_after_number:int = 0,             # начать читать строки начиная с указанной (счёт начинается с 1)
        stop_after_sequence:str = "",           # остановиться после того как встретится эта последовательность символов
        stop_after_number:int = 0,              # остановиться прочитав это количество строк файла
        store_max_count:int = 0,                # сохранить в результат не более N строк
        encoding:str = "utf-8"                  # кодировка файла
):
    result = []
    if not os.path.isfile(filename):
        return result
    with open(filename, "rt", encoding=encoding) as f:
        lines_count = 0
        begin_reading = begin_after_sequence == ""
        for s in f:
            lines_count += 1            
            if begin_after_number > 0 and lines_count < begin_after_number:
                continue # начинать чтение со строки с указанным номером
            if stop_after_number > 0 and lines_count > stop_after_number:
                break # продолжать чтение до строки с указанным номером
            if begin_reading and stop_after_sequence != "" and s.find(stop_after_sequence) >= 0:
                break # прекратить чтение как только встретится эта последовательность
            if not begin_reading and s.find(begin_after_sequence) >= 0:
                begin_reading = True
                if not begin_reading:
                    continue # ещё не встретилась последовательность, начиная с которой читать файл
            while len(s) > 0 and s[-1] in '\n\r':
                s = s[0:len(s)-1] # удалить переводы строки в конце строки
            s = remove_comment(s, comment_sequence) # удалить комментарии
            if strip_spaces_at_begins:
                s = s.lstrip() # удалить пробелы в начале
            if strip_spaces_at_ends:
                s = s.rstrip() # удалить пробелы в конце
            if skip_empty_lines and len(s) == 0:
                continue # пустая строка
            result.append(s)
            if store_max_count > 0 and len(result) >= store_max_count:
                break # в результат сохранено максимальное количество строк
    return result

#lines = file_to_array("notes.txt"); print(lines); exit(0)
#lines = file_to_array("notes.txt", stop_after_sequence="http"); print(lines); exit(0)
#lines = file_to_array("notes.txt", begin_after_number=2, stop_after_number=3); print(lines); exit(0)

# --- Получить имя файла из каталог изменявшегося позже всех (но исключая перечисленные в exclude[])---
def get_last_file(dirname:str, startswith:str = "", endswith:str = "", exclude = []) -> str:
    if os.path.isfile(dirname):
        # вместо каталога указан файл - выделить путь к каталогу
        dirname = os.path.dirname(dirname)
    if not os.path.isdir(dirname):
        return None
    if type(exclude) == type("abc"):
        # скаляр в массив из одного элемента
        exclude = {exclude}
    
    """
    # в exclude[] могут быть указаны относительные пути, добавить в этот список абсолютные
    tmp = exclude.copy()
    for s in exclude:
        abspath = os.path.abspath(s)
        if abspath != s:
            tmp.append(abspath)
    exclude = tmp.copy()
    del tmp
    """
    
    """
    не выполнять при каждом вызове
    # в exclude[] могут быть строки с полным или частичным путём к файлу - выделить только имя файла
    tmp = []
    for s in exclude:
        b = os.path.basename(s)
        if b not in tmp:
            tmp.append(b)
    exclude = tmp.copy()
    del tmp
    """

    files_and_dirs = os.listdir(dirname)
    last_file_path = None
    last_file_time = None
    for elem in files_and_dirs:
        current_path = os.path.join(dirname, elem)
        if not os.path.isfile(current_path):
            # объект каталога не является файлом
            continue
        if startswith != "":
            # указано начало имени файла
            if not elem.startswith(startswith):
                # имя текущего файла не начинается указанным префиксом - пропустить этот файл
                #print("skip1", elem)
                continue
        if endswith != "":
            # указано расширение файла
            if not elem.endswith(endswith):
                # имя текущего файла не заканчивается указанным расширением - пропустить этот файл
                #print("skip2", elem)
                continue
        #print("match", elem)
        if elem in exclude:
            # не учитывать текущий файл (короткое имя без каталога)
            continue
        if current_path in exclude:
            # не учитывать текущий файл (полный путь к файлу)
            continue
        current_file_time = os.path.getmtime(current_path)
        if last_file_time is None or current_file_time > last_file_time:
            last_file_path = current_path
            last_file_time = current_file_time
    return last_file_path

#print(get_last_file("/tmp", "", "", "/tmp/yandex_browser_updater.log")); exit(0)
#last_file = get_last_file("scan", "", "", "scan_2023-07-06_10-23-04.txt")
#last_file = get_last_file("scan", "", "", ["scan_2023-07-06_10-23-04.txt", "scan\scan_2023-07-06_10-22-36.txt"])
#print(last_file)
#exit(0)


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


# --- Находится ли имя файла или каталога в переданном списке имён и масок включающих символы * и ? ---
def check_name_matching(checking_name:str, names_or_masks) ->bool:
    if checking_name in names_or_masks:
        return True
    for mask in names_or_masks:
        if '*' in mask or '?' in mask:
            if fnmatch.fnmatch(checking_name, mask):
                return True
    return False

#print(check_for_skipping("file123.txt", ["file.txt", "file???.tx?"])); exit(0)

#print(os.path.isfile("/home/alexey/bin/1.sh")); exit(0)
#print(os.path.isfile("/home/alexey/bin/2.sh")); exit(0)
#print(os.path.isfile("/sources")); exit(0)
#print(os.path.islink("/sources")); exit(0)

def do_scan(root_dir, file_stream, args, skip, depth):
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
        if not os.path.isfile(path):
            continue # объект не является файлом
        if check_name_matching(one_item, skip):
            continue # имя объекта находится в списке игнорируемых объектов
        if check_name_matching(path, skip):
            continue # имя объекта находится в списке игнорируемых объектов
        if os.path.islink(path):
            # символическая ссылка
            line = path + '\t' + '=>' + '\t' + os.path.realpath(path)
            print_message(line, MESSAGE_KIND__RAW, args.print, file_stream)
        else:
            # файл
            line = get_file_attr_str(path, args)
            if not line is None:
                print_message(line, MESSAGE_KIND__RAW, args.print, file_stream)

    # +++ обработка каталогов root_dir +++
    for one_item in items:
        path = os.path.join(root_dir, one_item)
        if not os.path.isdir(path):
            continue # объект не является каталогом
        if check_name_matching(one_item, skip):
            continue # имя объекта находится в списке игнорируемых объектов
        if check_name_matching(path, skip):
            continue # имя объекта находится в списке игнорируемых объектов

        if os.path.islink(path) and not args.follow_symlinks:
            # ссылка на каталог и не включен переход по ссылкам - пропустить
            continue
        path += SLASH
        print_message(path, MESSAGE_KIND__RAW, args.print, file_stream)
        if args.max_depth is None or args.max_depth == 0 or depth < args.max_depth:
            do_scan(path, file_stream, args, skip, depth+1)


def inc_month(initial_date_time:datetime, months_count:int) -> datetime:
    #print(initial_date_time, "months_count=", months_count)
    if months_count > 0:
        sign = +1
    elif months_count < 0:
        sign = -1
    else:
        return initial_date_time
    months_count = abs(months_count)
    year    = initial_date_time.year
    month   = initial_date_time.month
    day     = initial_date_time.day
    hour    = initial_date_time.hour
    minute  = initial_date_time.minute
    second  = initial_date_time.second
    #print(year, month, day, hour, minute, second)
    # 14: 14/12=1 | 2
    if abs(months_count) > 12:
        inc_years = int(months_count / 12)
        inner_months = months_count % 12
    else:
        inc_years = 0
        inner_months = months_count
    #print(sign, inc_years, inner_months)
    year += sign*inc_years
    month += sign*inner_months
    if month > 12:
        year +=1 
        month = month - 12
    elif month < 1:
        year -= 1
        month = month + 12
    #print(year, month, day, hour, minute, second)
    target_date_time = None
    try:
        target_date_time = datetime.datetime(year, month, day, hour, minute, second)
    except:
        target_date_time = None
    if target_date_time is None:
        # не получилось изменить месяц, вероятно, потому что попали на числа, которых нет в целевом месяце (например, 31 февравля) - отбросить дни месяца
        try:
            target_date_time = datetime.datetime(year, month, 1, hour, minute, second)
        except:
            return None # не должно возникать
    
    return target_date_time
    
#print(inc_month(datetime.datetime.now(), -3)); exit(0)
#print(inc_month(datetime.datetime.now(), -14)); exit(0)
#print(inc_month(datetime.datetime(2025, 2, 28, 12,12,12, 1), -14)); exit(0)
#print(inc_month(datetime.datetime.now(), 4)); exit(0)
#print(inc_month(datetime.datetime.now(), -14)); exit(0)
#print(inc_month(datetime.datetime(2025, 12, 31, 12,12,12, 1), 14)); exit(0)

def inc_year(initial_date_time:datetime, years_count:int) -> datetime:
    return inc_month(initial_date_time, 12*years_count)

#print(inc_year(datetime.datetime.now(), -10)); exit(0)

def get_date_time_by_age(age_str: str) -> datetime:
    age_str = age_str.lower()
    age_value = ""
    age_measure = ""
    i = len(age_str) - 1
    while i >= 0 and age_str[i] not in "0123456789":
        i -= 1
    age_value = age_str[0:i+1]
    age_value = age_value.strip()
    age_measure = age_str[i+1:len(age_str)]
    age_measure = age_measure.strip()
    try:
        age_value_int = int(age_value)
    except:
        return None
    measure_multiplicator = 1
    target_date_time = None
    if len(age_measure) > 0:
        # указана единица измерения (если не указана - секунды)
        if age_measure in ["s", "sec", "second", "seconds"]:
            measure_multiplicator = 1
        if age_measure in ["m", "min", "mins", "minute", "minutes"]:
            measure_multiplicator = 60
        elif age_measure in ["h", "hour", "hours"]:
            measure_multiplicator = 3600
        elif age_measure in ["d", "day", "days"]:
            measure_multiplicator = 86400
        elif age_measure in ["w", "week", "weeks"]:
            measure_multiplicator = 432000
        elif age_measure in ["mn", "mon", "month", "months"]:
            target_date_time = inc_month(datetime.datetime.now(), -age_value_int)
        elif age_measure in ["y", "year", "years"]:
            target_date_time = inc_year(datetime.datetime.now(), -age_value_int)
    if target_date_time is None:
        target_date_time = datetime.datetime.now() - datetime.timedelta(seconds=measure_multiplicator*age_value_int)
    return target_date_time

#print(get_date_time_by_age("15 month")); exit(0)


def remove_ending_symbols(s: str, removable_symbols: str) -> str:
    while len(s) > 0 and s[-1] in removable_symbols:
        s = s[0:len(s)-1]
    return s

#print(os.path.join("/dir1/", "file1.txt")); exit(0)

def get_output(filename, command, append):
    if filename is None:
        return None
    if filename == '':
        return None
    if filename[-1] in ['\\', '/']:
        # указан каталог, в котором создать новый файл
        dirname = remove_ending_symbols(filename, "\\/")
        if dirname == '':
            # был указан корневой каталог unix-а
            dirname = "/"
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        filename_short = command + "_" + get_timestamp(None, "-", "_", "-") + ".dat"
        filename = os.path.join(dirname, filename_short)

    #print("!!!", filename); exit(0)
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
    f.close()


def age_one_measure(age, measure):
    if age.lower().endswith(measure):
        value_str = age[0:len(age)-len(measure)]
        if value_str == '':
            value_int = 1
        else:
            value_int = int(value_str)


# Из строки вида <dd.mm.yyyy[ hh:mm:ss]> или <yyyy.mm.dd[ hh:mm:ss]> получить дату; если недопустимый формат - вернуть None
def str_to_date_time(s:str) ->datetime:
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
    
#d1 = str_to_date_time("31.12.2012 08:11:59"); print(d1); exit(0)
#d1 = str_to_date_time("2012-12-31 09:11:59"); print(d1); exit(0)
#d1 = str_to_date_time("2012-02-31 09:11:59"); print(d1); exit(0)

"""
# ----- В объекте типа datetime.datetime изменить месяц -----
def inc_months(sourcedate, months):
    import calendar
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.datetime(year, month, day, sourcedate.hour, sourcedate.minute, sourcedate.second, sourcedate.microsecond)
"""

"""
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
"""
    
def prepare_arguments(args):
    if (args.print == False or args.print is None) and args.output is None:
        args.print = True
    args._skip_before = None
    args._skip_after = None
    if not args.min_age is None:
        args._skip_after = get_date_time_by_age(args.min_age)
    if not args.max_age is None:
        args._skip_before = get_date_time_by_age(args.max_age)
    if not args.min_time is None:
        d = str_to_date_time(args.min_time)
        if not d is None:
            args._skip_before = d
    if not args.max_time is None:
        d = str_to_date_time(args.max_time)
        if not d is None:
            args._skip_after = d
    return args

def get_skipping_items(args):
    skip = DEFAULT_SKIP.copy()

    # добавить отдельные маски перечисленные в параметрах --skip
    for elem in args.skip:        
        skip.append(elem)

    # добавить маски перечисленные в файлах указанных в параметрах --skip-from
    for elem in args.skip_from:
        skip_from = file_to_array(elem)
        skip += skip_from

    skip = set(skip)
    #print(skip); exit(0)
    return skip

# X = ["aaa", "AAA", "a1", "a2", "aaa", "", "BBB"]
# Y = ["bbb", "BBB"]
# X += Y;  print("X as array:", X)
# X = set(X)
# print("X as set:", X)
# exit(0)


if __name__ == "__main__":
    #print("argv:", sys.argv); exit(0)
    #f1();exit(0)
    #parser = f2a()
    if os.path.isfile('/etc/passwd'):
        SLASH = '/'
    else:
        SLASH = '\\'
    parser = get_arg_parser_definiton()
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
    print("args:", args); #exit(0)

    if args.command == 'help':
        print('help...')
        parser.print_help()
    elif args.command == 'scan':
        print('scan...')
        #print("output:", args.output)
        #print("dirs[]:", args.directory)
        f = get_output(args.output, args.command, args.append)
        #print('output:', f)
        skip = get_skipping_items(args)
        for d in args.directory:
            do_scan(d, f, args, skip, INITIAL_DEPTH)
        close_output(f, args.command)
    elif args.command == 'compare':
        print('compare...')
        f = get_output(args.output, args.command, args.append)
    exit(0)

    parser = get_parser_definiton()
    #args = parser.parse_args()
    parser.print_help()
