#!/usr/bin/env python3

import sys
import argparse
import os
import datetime
import hashlib
import zlib
import fnmatch
import shutil
#import re


INITIAL_DEPTH = 1
SLASHES = '\\/'
SLASH = "|"
HASH_METHODS = ['crc32', 'md5', 'sha256', 'sha512', 'sha384', 'sha1']
DEFAULT_HASH_METHOD = HASH_METHODS[0]
FILES_DEFAULT_ENCODING = 'utf-8'

#MESSAGE_KIND__LOG = "l"
#MESSAGE_KIND__VERBOSE = "i"
MESSAGE_KIND__COMMENT = "c"
MESSAGE_KIND__DEBUG = "d"
MESSAGE_KIND__INFO = "i"
MESSAGE_KIND__WARNING = "w"
MESSAGE_KIND__ERROR = "e"
MESSAGE_KIND__FATAL = "f"
MESSAGE_KIND__QUESTION = "q"
MESSAGE_KIND__RAW = "r"
COMMENT_SYMBOL = "#"

_sn = 0
LOGGING_LEVEL__ALL = _sn; _sn += 1          # 0
LOGGING_LEVEL__DEBUG = _sn; _sn += 1        # 1
LOGGING_LEVEL__INFO = _sn; _sn += 1         # 2
LOGGING_LEVEL__WARNING = _sn; _sn += 1      # 3
LOGGING_LEVEL__ERROR = _sn; _sn += 1        # 4
LOGGING_LEVEL__FATAL = _sn; _sn += 1        # 5
LOGGING_LEVEL__OFF = _sn; _sn += 1          # 6
LOGGING_LEVEL = LOGGING_LEVEL__WARNING

PREFIX_SCAN = "scan_"
PREFIX_COMPARE = "compare_"
PREFIX_BUILD = "build_"
DEFAULT_EXTENSION = ".txt"

DEBUG_MODE = False
_DEBUG_ARGS = []
if DEBUG_MODE:
    #_DEBUG_ARGS = ["scan",  "-o", "/tmp/scan2.txt", "--append", "--size", "/tmp", "/var"]
    #_DEBUG_ARGS = ["scan",  "-o", "/tmp/scan1.txt", "--size", "-T", "-H", "--follow-symlinks", "--min-size=1000", "/tmp"]
    #_DEBUG_ARGS = ["scan",  "-o", "/tmp/scan1.txt", "--size", "-T", "-H", "--follow-symlinks", "--min-size=1000", "--min-age", "10d", "--min-time=2025.02.01", "/tmp"]
    #_DEBUG_ARGS = ["compare", "--input", "/home/alexey/bin/scan/results1", "-o", "/home/alexey/bin/compare/results/"]
    #_DEBUG_ARGS = ["compare", "--input", "/tmp/scan1.txt", "--input", "/tmp/scan2.txt", "-o", "/tmp/compare_results/"]
    #_DEBUG_ARGS = ["compare", "--input=./scan_results/", "--output=./compare_results/"]
    #_DEBUG_ARGS = ["build", "--input=./compare_results", "--output=./build/"]
    _DEBUG_ARGS = ["build", "--input=compare_results", "--output=build/", '--note="Текст для Комментария"']
    pass



# убрать миллисекунды после конвертирования даты в строку: datetime.datetime.utcnow().strftime('%F %T.%f')[:-3]
#print( datetime.datetime.now().strftime('%F %T.%f')[:-3] ); exit(0) # - не работает

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


def get_arg_parser_definiton():
    parser = argparse.ArgumentParser(
        prog = 'get_files_list',
        description = """Выяснение списка изменившихся файлов в ходе выполнения каких-либо действий на компьютере, например, установки или настройки программы.
1) Составить список файлов до установки или настройки программы (состояние "А") - команда "scan";
2) Произвести установку или настройку программы;
3) Составить список файлов (состояние "Б") - команда "scan";
4) Сравнить два списка файлов, результаты записать в файл различий - команда "compare";
5) На основе файла различий собрать установочный пакет приводящий систему из состояния "А" в состояние "Б" - команда "build".""",
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
    parser_scan.add_argument('--skip', nargs='*', action='extend', help='Игнорировать файл или каталог соответствующий маске')
    parser_scan.add_argument('--skip-from', nargs='*', action='extend', help='Маски игнорируемых файлов или каталогов прочитать из файла. Каждая строка файла содержит одну маску. Комментарий - #')
    parser_scan.add_argument('-n', '--note', help='Комментарий записываемый в файл результата')
    parser_scan.add_argument('directory', nargs='+', help='Сканируемый каталог (можно указать несколько через пробел)')

    parser_compare = subparsers_commands.add_parser('compare', help='Сравнение двух результатов сканирования')
    parser_compare.add_argument('-p', '--print', action='store_true', help='Вывод на экран, даже если выполняется вывод в файл (при наличии параметра -o | --output <filename>)')
    parser_compare.add_argument('-a', '--append', action='store_true', help='Если файл результатов существует - добавить в него вместо создания нового')
    parser_compare.add_argument('-i', '--input', nargs='+', action='extend', help='Файл с результатами сканирования. Должен указываться либо дважды при указании двух файлов, либо содержать имя каталога из которого будут взяты два последних по дате файла с маской "scan_*.txt". Если не указан - последние файлы с маской scan_*.txt в текущем каталоге')
    parser_compare.add_argument('-o', '--output', help='Файл с результатами сравнения. Если не указан - вывод в <stdout>')
    parser_compare.add_argument('-n', '--note', help='Комментарий записываемый в файл результата')

    parser_build = subparsers_commands.add_parser('build', help='Создать установочные файлы для применения изменений')
    parser_build.add_argument('-i', '--input', help='Файл с результатами сравнения. Если не указан - последний файл в текущем каталоге. Если каталог - последний файл из каталога')
    parser_build.add_argument('-o', '--output', help='Каталог, в котором создать файлы для воспроизведения изменений. Если не указан - создать подкаталог build в текущем каталоге')
    parser_build.add_argument('-n', '--note', help='Комментарий записываемый в файл результата')

    return parser


def fill_advanced_hash_methods(methods) -> None:
    for x in hashlib.algorithms_available:
        if x not in methods:
            methods.append(x)
fill_advanced_hash_methods(HASH_METHODS)
#print(HASH_METHODS); exit(0)



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
    result = ''
    if not os.path.isfile(filename):
        return result
    if method == 'crc32':
        # +++ crc32 with zlib +++
        result = get_hash__crc32(filename)
    elif method in hashlib.algorithms_available:
        # +++ алгоритмы из hashlib +++
        BLOCK_SIZE = 2**20
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


def file_to_array__simple(filename, comment_sequence = '', skip_empty_lines = False):
    result = []
    with open(filename, "rt") as f:
        for s in f:
            s = s.strip()
            if len(comment_sequence) > 0:
                # удалить однострочные комментарии
                p = s.find(comment_sequence)
                if p >= 0:
                    s = s[0:p]
            if len(s) == 0 and skip_empty_lines:
                continue # пустая строка
            result.append(s)
    return result

#lines = file_to_array("/etc/fstab", '#', True); from pprint import pprint;  pprint(lines); exit(0)

#print("abc".replace("b", "BB")); exit(0)

#---------------- Удалить комментарий начнающийся с comment_sequence -------------
def remove_comment(s:str, comment_sequence:str = COMMENT_SYMBOL) -> str:
    p = s.find(comment_sequence)
    if p >= 0:
        s = s[0:p]
    return s

#print(remove_comment("str//oka", "//")); exit(0)
#print(remove_comment("str # oka", "#")); exit(0)

def scalar_to_tuple(x):
    if type(x) == type(()):
        return x # уже является кортежом
    if type(x) == type([]):
        return x # уже является списком
    if x is None:
        return () # None заменить на пустой кортёж
    return (x, )

#x = 123.456; y = scalar_to_tuple(x); print(type(y)); print(len(y)); print(y); exit(0)
#x = None; y = scalar_to_tuple(x); print(type(y)); print(len(y)); print(y); exit(0)

# --- Прочитать строки файла в массив ---
def file_to_array(
        filename:str,                           # имя читаемого файла
        comment_sequence:str = '',              # начало однострочного комментария, начиная с которого удалять до конца строки
        strip_spaces_at_begins:bool = False,    # удалять пробельные символы в начале строк
        strip_spaces_at_ends:bool = False,      # удалять пробельные символы в конце строк
        replaces = {},                          # выполнить замены (ключ - что искать, значение - на что заменить)
        ignore_empty:bool = False,              # пропускать пустые строки          ignore_... ?

        max_count:int = -1,                     # сохранить в результат не более N строк
        max_length:int = -1,                    # максимальная длина каждой строки (после удаления пробелов, комментариев и всех трансформаций)
        numerate_lines_since = 0,               # нумеровать строки с этого значения (обычно 0 или 1, но можно и другое)

        accept_while = (),      # принимать только строки содержащие эти последовательности символов или находящиеся в строках файла этими номерами
        accept_since = (),      # начать принимать строки, когда встретится указанная последовательность или начиная с указаной строки файла
        accept_after = (),      # начать принимать следующие строки, когда встретится указанная последовательность или начиная с указаной строки файла

        ignore_while = (),      # пропускать строки содержащие эти последовательности символов или находящиеся в строках файла этими номерами
        ignore_since = (),
        ignore_after = (),

        break_at = (),          # немедленно остановить чтение файла, текущая строка не добавляется
        break_after = (),       # остановить чтение со следующей строки, если текущая строка должна быть добавлена - добавить её

        encoding:str = FILES_DEFAULT_ENCODING   # кодировка файла
):
    def _modifications():
        nonlocal s
        while len(s) > 0 and s[-1] in ['\n', '\r']:
            # удалить переводы строк
            s = s[0:len(s)-1]
        if strip_spaces_at_begins:
            # удалить пробелы в начале
            s = s.lstrip()
        if strip_spaces_at_ends:
            # удалить пробелы в конце
            s = s.rstrip()
        if len(comment_sequence) > 0:
            # удалить комментарии начиная с этой последовательности означающей однострочный комментарий до конца строки
            p = s.find(comment_sequence)
            if p >= 0:
                s = s[0:p]
        if len(replaces) > 0 and len(s) > 0:
            # определён список замен
            for key in replaces.keys():
                value = replaces[key]
                value = value.replace('${line_number}', str(line_number))
                s = s.replace(key, value)
        if max_length >= 0:
            # укоротить строку до max_length символов
            s = s[0:max_length]

    def _in_array(checking_value, items, allow_partial_matching_for_strings:bool = False):
        for x in items:
            if checking_value == x:
                return True
            if allow_partial_matching_for_strings and type(checking_value) == type("abc"):
                if x.find(checking_value) >= 0:
                    return True
        return False
    
    def _from_list(text_value, number_value, items):
        for x in items:
            if type(x) == type("abc"):
                if text_value.find(x) >= 0:
                    return True
            elif type(x) == type(123):
                if x == number_value:
                    return True
        return False

    def _checks():
        nonlocal s
        nonlocal line_number
        nonlocal state
        line = s
        if ignore_empty and len(s) == 0:
            return False
        # не пустая строка, значит можно применять к ней проверки
        accept_this_line = state == STATE__ACCEPT
        if len(ignore_while) > 0:
            if _from_list(line, line_number, ignore_while):
                return False
        if len(accept_while) > 0:
            if not _from_list(line, line_number, accept_while):
                return False
        if len(accept_after) > 0:
            if _from_list(line, line_number, accept_after):
                state == STATE__ACCEPT
        if len(accept_since) > 0:
            if _from_list(line, line_number, accept_since):
                accept_this_line = True
                state == STATE__ACCEPT
        if len(ignore_after) > 0:
            if _from_list(line, line_number, ignore_after):
                state == STATE__IGNORE
        if len(ignore_since) > 0:
            if _from_list(line, line_number, ignore_since):
                accept_this_line = False
                state == STATE__IGNORE
        if len(break_at) > 0:
            if _from_list(line, line_number, break_at):
                accept_this_line = False
                state = STATE__BREAK
        if len(break_after) > 0:
            if _from_list(line, line_number, break_after):
                state = STATE__BREAK
        return accept_this_line
        

    STATE__ACCEPT = 'a'
    STATE__IGNORE = 'i'
    STATE__BREAK = 'b'
    result = []
    if not os.path.isfile(filename):
        return None
    accept_while = scalar_to_tuple(accept_while)
    accept_since = scalar_to_tuple(accept_since)
    accept_after = scalar_to_tuple(accept_after)

    ignore_while = scalar_to_tuple(ignore_while)
    ignore_since = scalar_to_tuple(ignore_since)
    ignore_after = scalar_to_tuple(ignore_after)

    break_at = scalar_to_tuple(break_at)
    break_after = scalar_to_tuple(break_after)

    with open(filename, "rt", encoding=encoding) as f:
        lines_count = 0
        if len(accept_since) > 0 or len(accept_after) > 0:
            # принимать строки только после некоторого критерия, сначала строки не принимаются
            state = STATE__IGNORE
        else:
            state = STATE__ACCEPT
        for s in f:
            lines_count += 1
            line_number = lines_count - 1 + numerate_lines_since
            _modifications()
            if _checks():
                result.append(s)
                if max_count >= 0 and len(result) >= max_count:
                    # прочитано необходимое количество строк
                    break
            if state == STATE__BREAK:
                break
    return result


#lines = file_to_array("notes.txt"); print(lines); exit(0)
#lines = file_to_array("notes.txt", comment_sequence='#', ignore_empty=True, break_at='zzz', max_count=3); print(lines); exit(0)

# --- Получить имя файла из каталог изменявшегося позже всех (но исключая перечисленные в exclude[])---
def get_last_file(dirname:str, startswith:str = "", endswith:str = "", exclude = {}) -> str:
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
    if args.time:
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

#print(get_timestamp(None, "-", "T", ":")); exit(0)

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

def remove_starting_symbols(s: str, removable_symbols) -> str:
    while len(s) > 0 and s[0] in removable_symbols:
        s = s[1:len(s)]
    return s

def remove_ending_symbols(s: str, removable_symbols) -> str:
    while len(s) > 0 and s[-1] in removable_symbols:
        s = s[0:len(s)-1]
    return s

def remove_starting_slashes(s:str) -> str:
    return remove_starting_symbols(s, SLASHES)

def remove_ending_slashes(s:str) -> str:
    return remove_ending_symbols(s, SLASHES)


def defined(x, other_undefined = (), all_defined = ()):
    if x is None:
        return False
    if x == '':
        return False
    if len(other_undefined) > 0:
        # указаны другие значения, при которых считать значение "x" неопределённым
        if x in other_undefined:
            return False
    if len(all_defined) > 0:
        # указан список в который должно входить значение "x", чтобы считаться определённым
        if x in all_defined:
            return True
        return False
    return True

#print(defined(123, (132, 1231), (456,))); exit(0)
#print('matched') if 0 == '' else print('not matched'); exit(0)

def prepare_message(message:str, kind:str = '') -> str:
    if not defined(message):
        return '' # не указан текст сообщения
    message = message.strip()
    message = remove_starting_symbols(message, COMMENT_SYMBOL) # если комментарий уже указан - удалить его, т.к. будет добавляться префикс с типом сообщения
    message = message.strip()
    if not defined(message):
        return '' # после удавления пробелов в начале и конце и символов комментария получилась пустая строка
    if message[0].islower():
        # перевести первый символ в верхний регистр, если он в нижнем
        message = message.capitalize()
    punctuation_symbol = ''
    this_message_logging_level = None
    if kind == MESSAGE_KIND__QUESTION:
        message = '[' + get_timestamp() + '] ' + 'QUESTION: ' + message
        punctuation_symbol = '?'
    elif kind == MESSAGE_KIND__DEBUG:
        this_message_logging_level = LOGGING_LEVEL__DEBUG   # 1
        message = '[' + get_timestamp() + '] ' + 'DEBUG: ' + message
    elif kind == MESSAGE_KIND__INFO:
        this_message_logging_level = LOGGING_LEVEL__INFO    # 2
        message = '[' + get_timestamp() + '] ' + 'INFO: ' + message
        punctuation_symbol = "."
    elif kind == MESSAGE_KIND__WARNING:
        this_message_logging_level = LOGGING_LEVEL__WARNING # 3
        message = '[' + get_timestamp() + '] ' + 'WARNING! ' + message
        punctuation_symbol = '!'
    elif kind == MESSAGE_KIND__ERROR:
        this_message_logging_level = LOGGING_LEVEL__ERROR   # 4
        message = '[' + get_timestamp() + '] ' + 'ERROR!! ' + message
        punctuation_symbol = '!'
    elif kind == MESSAGE_KIND__FATAL:
        this_message_logging_level = LOGGING_LEVEL__FATAL   # 5
        message = '[' + get_timestamp() + '] ' + 'FATAL_ERROR!!! ' + message
        punctuation_symbol = "!"
    if defined(this_message_logging_level) and this_message_logging_level < LOGGING_LEVEL:
        # более серьёзные сообщения имеют больший номер, а уровень текущего сообщения не дотягивает до заданного уровня
        return ''
    if defined(punctuation_symbol) and message[-1] not in ('.', '!', '?'):
        message += punctuation_symbol # если строка не заканчивется символом пунктуации, то поставить соответствующий типу сообщения знак пунктуации
    message = COMMENT_SYMBOL + ' ' + message
    return message

#print(prepare_message('  #   привет  ', MESSAGE_KIND__QUESTION)); exit(0)

def print_message(message:str, kind:str = MESSAGE_KIND__RAW, display:bool = True, file_stream:any = None) -> None:
    if kind == MESSAGE_KIND__RAW:
        if display:
            print(message)
        if not file_stream is None:
            file_stream.write(message + '\n')
    else:
        message = prepare_message(message)
        if not defined(message):
            return
        if not file_stream is None:
            file_stream.write(message + '\n')
        if kind == MESSAGE_KIND__FATAL:
            raise Exception(message)
        elif kind == MESSAGE_KIND__ERROR:
            # ошибки выводятся в поток ошибок
            print(message, file=sys.stderr)
        else:
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



#print(remove_ending_slashes("hello \\df/\/")); exit(0)
#print(remove_starting_slashes("/\\hello \\df/\/")); exit(0)

#print(os.path.join("/dir1/", "file1.txt")); exit(0)

def get_output(filename, command, append, note):
    if filename is None:
        return None
    if filename == '':
        return None
    if filename[-1] in ['\\', '/']:
        # указан каталог, в котором создать новый файл; если каталог не существует - создать его
        filename = remove_ending_slashes(filename)
        if filename == '':
            # был указан корневой каталог unix-а
            filename = "/"
        if not os.path.isdir(filename):
            os.makedirs(filename)
    if os.path.isdir(filename):
        filename_short = command + "_" + get_timestamp(None, "-", "_", "-") + DEFAULT_EXTENSION
        filename = os.path.join(filename, filename_short)

    #print("!!!", filename); exit(0)
    if append:
        mode = 'at'
    else:
        mode = 'wt'
    f = open(filename, mode, encoding=FILES_DEFAULT_ENCODING)
    msg = '\t'
    msg += '---'
    msg  += ' [' + get_timestamp() + ']'
    msg += ' Begin ' + command
    msg += ' ---'
    print_message(msg, MESSAGE_KIND__COMMENT, False, f)
    if not note is None and note != '':
        print_message(note, MESSAGE_KIND__COMMENT, False, f)
    #print("OUTPUT:", filename, f)
    return f

def close_output(f, command):
    if not f is None:
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
    if "print" in args:
        if (args.print is None or args.print == False) and args.output is None:
            # если нет вывода в файл - принудительно выводить на экран
            args.print = True
    if args.command == 'scan':
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


def is_array_or_tuple(x:any) -> bool:
    if x is None:
        return False
    if type(x) == type([]):
        return True
    if type(x) == type(()):
        return True
    return False

#print(is_array_or_tuple(None)); exit(0)
#print(is_array_or_tuple("a")); exit(0)
#print(is_array_or_tuple(["a", 123])); exit(0)
#print(is_array_or_tuple(("a", 123))); exit(0)
#print(is_array_or_tuple({"key" : 123})); exit(0)

def get_skipping_items(args):
    skip = DEFAULT_SKIP.copy()

    # добавить отдельные маски перечисленные в параметрах --skip
    if is_array_or_tuple(args.skip):
        for elem in args.skip:        
            skip.append(elem)

    # добавить маски перечисленные в файлах указанных в параметрах --skip-from
    if is_array_or_tuple(args.skip_from):
        for elem in args.skip_from:
            skip_from = file_to_array(elem, comment_sequence=COMMENT_SYMBOL, ignore_empty=True)
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


# --- Прочитать результаты сканирования ---
def read_scan_results(filename:str):
    result = {}
    f = open(filename, 'rt', encoding=FILES_DEFAULT_ENCODING)
    for s in f:
        s = s.strip()
        #s = s.lstrip() # удалить ведущие пробелы
        #s = s.rstrip("\n") # удалить переводы строк
        #s = s.rstrip("\r") # удалить переводы строк
        s = remove_comment(s, COMMENT_SYMBOL)
        if len(s) == 0:
            continue # пустая строка
        p = s.find("\t")
        if p > 0:
            # строка, где до первой табуляции - путь, а после атрибуты
            #ab|cd
            #01234
            path = s[0:p]
            attr = s[p+1:len(s)]
            result[path] = attr
        else:
            # только путь без атрибутов (либо это каталог, либо для файлов атрибуты не запрашивались)
            result[s] = ""
    f.close()
    return result


def do_compare(args):
    old_scan_file = None   # файл с результатами сканирования до изменений
    new_scan_file = None   # файл с результатами сканирования после изменений
    if len(args.input) == 0:
        # не указаны файлы с результатами сканирования, искать последние два файла в текущем каталоге
        new_scan_file = get_last_file(".", PREFIX_SCAN, DEFAULT_EXTENSION)
        old_scan_file = get_last_file(".", PREFIX_SCAN, DEFAULT_EXTENSION, new_scan_file)
    elif len(args.input) == 1:
        # указан один input-параметр (если один - это должен быть каталог, из которого взять два последних файла)
        if not os.path.isdir(args.input[0]):
            raise Exception('"{}" is not directory or not exist.' . format(args.input[0]))
        new_scan_file = get_last_file(args.input[0], PREFIX_SCAN, DEFAULT_EXTENSION)
        old_scan_file = get_last_file(args.input[0], PREFIX_SCAN, DEFAULT_EXTENSION, new_scan_file)
    elif len(args.input) >= 2:
        # указаны два input-параметра. Если указан каталог - взять последний файл, если файл - этот файл
        # первый параметр - до изменений, второй параметр - после изменений
        if os.path.isdir(args.input[0]):
            old_scan_file = get_last_file(args.input[0], PREFIX_SCAN, DEFAULT_EXTENSION)
        else:
            old_scan_file = args.input[0]
        if os.path.isdir(args.input[1]):
            new_scan_file = get_last_file(args.input[0], PREFIX_SCAN, DEFAULT_EXTENSION)
        else:
            new_scan_file = args.input[0]

    old_scan_results = read_scan_results(old_scan_file)
    new_scan_results = read_scan_results(new_scan_file)
    old_names_list = list(old_scan_results.keys())
    new_names_list = list(new_scan_results.keys())
    deleted = []
    created = []
    updated = []

    # поиск удалённых
    for elem in old_names_list:
        if elem not in new_scan_results:
            deleted.append(elem)

    # поиск созданных или обновлённых
    for elem in new_names_list:
        if elem in old_scan_results:
            # файл/каталог присутствует в обоих списках
            if new_scan_results[elem] != old_scan_results[elem]:
                # файл изменился
                updated.append(elem)
        else:
            # новый файл/каталог
            created.append(elem)


    f = get_output(args.output, args.command, args.append, args.note)

    #msg = '\t----- [{}]  Difference for "{}" and "{}" ---' . format(get_timestamp(), prev_scan_file, next_scan_file)
    #msg = 'Difference for "{}" and "{}" ---' . format(prev_scan_file, next_scan_file)
    msg = 'File#1 (before): "{}"' . format(old_scan_file)
    print_message(msg, MESSAGE_KIND__COMMENT, args.print, f)
    msg = 'File#2 (after): "{}"' . format(new_scan_file)
    print_message(msg, MESSAGE_KIND__COMMENT, args.print, f)
    print_message('', MESSAGE_KIND__RAW, args.print, f)

    msg = '\t--- Deleted ({}) ---' . format(len(deleted))
    print_message(msg, MESSAGE_KIND__COMMENT, args.print, f)
    for elem in deleted:
        msg = 'deleted' + '\t' + elem
        if old_scan_results[elem] != '':
            msg += '\t' + old_scan_results[elem]
        print_message(msg, MESSAGE_KIND__RAW, args.print, f)
    print_message('', MESSAGE_KIND__RAW, args.print, f)

    msg = '\t--- created ({}) ---' . format(len(created))
    print_message(msg, MESSAGE_KIND__COMMENT, args.print, f)
    for elem in created:
        msg = 'created' + '\t' + elem
        if new_scan_results[elem] != '':
            msg += '\t' + new_scan_results[elem]
        print_message(msg, MESSAGE_KIND__RAW, args.print, f)
    print_message('', MESSAGE_KIND__RAW, args.print, f)

    msg = '\t--- Updated ({}) ---' . format(len(updated))
    print_message(msg, MESSAGE_KIND__COMMENT, args.print, f)
    for elem in updated:
        msg = 'updated' + '\t' + elem + '\t' + old_scan_results[elem] + '\t=>\t' + new_scan_results[elem]
        print_message(msg, MESSAGE_KIND__RAW, args.print, f)
    #print_message('\t-----', MESSAGE_KIND__COMMENT, args.print, f)
        print_message('', MESSAGE_KIND__RAW, args.print, f)
    close_output(f, args.command)


def make_slashes__windows(s):
    if len(s) > 0 and s[0] == '/':
        s = '%SYSTEMDRIVE%' + s
    return s.replace('/', '\\')

#print(make_slashes__windows('/var/tmp/file1.txt')); exit(0)

def make_slashes__unix(s):
    return s.replace('\\', '/')

def make_slashes__current(s):
    if SLASH == '/':
        return make_slashes__unix(s)
    elif SLASH == '\\':
        return make_slashes__windows(s)
    return s # не должно возникать


def do_build__delete(output_root_dir, fu, fw, items):
    fu.write('# --- delete ---\n')
    fw.write('rem --- delete ---\n')
    for elem in items:
        # удаляемые каталоги
        if elem[-1] in SLASHES:
            # каталог
            elem = remove_ending_slashes(elem)
            dirname_unix    = make_slashes__unix(elem)
            dirname_windows = make_slashes__windows(elem)
            fu.write('if [ -d "{}" ]; then rm -r -f "{}"; fi\n'. format(dirname_unix, dirname_unix))
            fw.write('if exist "{}" rmdir /s /q "{}"\n' . format(dirname_windows, dirname_windows))
    for elem in items:
        # удаляемые файлы
        if not elem[-1] in SLASHES:
            # файл
            filename_unix    = make_slashes__unix(elem)
            filename_windows = make_slashes__windows(elem)
            fu.write('if [ -f "{}" ]; then rm "{}"; fi\n' . format(filename_unix, filename_unix))
            fw.write('if exist "{}" del /f /q "{}"\n' . format(filename_windows, filename_windows))
    fu.write('\n')
    fw.write('\n')


def do_build__update(output_root_dir, fu, fw, items):
    fu.write('# --- update ---\n')
    fw.write('rem --- update ---\n')
    for elem in items:
        # "обновляемые" каталоги; не должно возникать, но если есть обрабатывать как создаваемые
        if elem[-1] in SLASHES:
            # каталог
            elem = remove_ending_slashes(elem)
            dirname_unix    = make_slashes__unix(elem)
            dirname_windows = make_slashes__windows(elem)
            fu.write('if [ ! -d "{}" ]; then mkdir "{}"; fi\n' . format(dirname_unix, dirname_unix))
            fw.write('if not exist "{}" mkdir "{}"\n' . format(dirname_windows, dirname_windows))
    for elem in items:
        # обновляемые файлы
        if not elem[-1] in SLASHES:
            # файл
            write__copy_file(output_root_dir, elem, fu, fw)

    fu.write('\n')
    fw.write('\n')


def do_build__create(output_root_dir, fu, fw, items):
    fu.write('# --- create ---\n')
    fw.write('rem --- create ---\n')
    for elem in items:
        # новые каталоги
        if elem[-1] in SLASHES:
            # каталог
            elem = remove_ending_slashes(elem)
            dirname_unix    = make_slashes__unix(elem)
            dirname_windows = make_slashes__windows(elem)
            fu.write('if [ ! -d "{}" ]; then mkdir "{}"; fi\n' . format(dirname_unix, dirname_unix))
            fw.write('if not exist "{}" mkdir "{}"\n' . format(dirname_windows, dirname_windows))
    for elem in items:
        # новые файлы
        if not elem[-1] in SLASHES:
            # файл
            write__copy_file(output_root_dir, elem, fu, fw)
    fu.write('\n')
    fw.write('\n')


def parse_filename(s):
    dirname = ''
    filename = ''
    i = len(s) - 1
    while i >= 0:
        if s[i] in SLASHES:
            break
        i -= 1
    # ab\cd.txt         c:\temp\file1.txt  => disk_C\temp\file1.txt
    # 012345678  {9}
    dirname = s[0:i]
    filename = s[i+1:len(s)]
    if len(dirname) >= 2:
        if dirname[1] == ':':
            dirname = 'disk_' + dirname[0].upper() + dirname[2:len(dirname)]
    #if SLASH == '/':
    #    # скрипт работает на unix, заменить виндовые слеши
    #    dirname = dirname.replace('\\', '/')
    #elif SLASH == '\\':
    #    dirname = dirname.replace('/', '\\')
    return (dirname, filename)

#print(parse_filename("c:\\temp\\file1.txt")); exit(0)
#print(parse_filename("c:\\temp\\file1")); exit(0)
#print(parse_filename("/tmp")); exit(0)
#print(parse_filename("/tmp/file.zip")); exit(0)


def write__copy_file(output_root_dir, src_filename, fu, fw):
    (dirname_build_short, filename_build_short) = parse_filename(src_filename) 
    dirname_build_short = make_slashes__current(dirname_build_short)
    dirname_build_in_output = output_root_dir + SLASH + dirname_build_short
    if not os.path.exists(dirname_build_in_output):
        os.makedirs(dirname_build_in_output)
    filename_build_in_output = dirname_build_in_output + SLASH + filename_build_short
    copy_cmd_unix = 'cp -p -f "{}" "{}"'.format(
        make_slashes__unix(filename_build_in_output),
        make_slashes__unix(src_filename)
    )
    copy_cmd_windows = 'copy /Y "{}" "{}"'.format(
        make_slashes__windows(filename_build_in_output),
        make_slashes__windows(src_filename)
    )
    if os.path.isfile(src_filename):
        # есть с чего делать копию в каталоге "build"
        shutil.copy2(src_filename, filename_build_in_output)
        fu.write(copy_cmd_unix + '\n')
        fw.write(copy_cmd_windows + '\n')
    else:
        fu.write('# !!! file does not exist ' + copy_cmd_unix + '\n')
        fw.write('rem !!! file does not exist ' + copy_cmd_windows + '\n')


def do_build(args):
    scan_results_file = None
    if args.input is None:
        # не указан файл с результатами сравнения (или каталог с этим файлом) - взять последний файл из текущего каталога
        scan_results_file = get_last_file(".", PREFIX_COMPARE, DEFAULT_EXTENSION)
        if scan_results_file is None:
            msg = 'Cannot detect file with scan results in current directory.'
            raise Exception(msg)
    elif os.path.isdir(args.input):
        scan_results_file = get_last_file(args.input, PREFIX_COMPARE, DEFAULT_EXTENSION)
        if scan_results_file is None:
            msg = 'Cannot detect file with scan results in "{}" directory.' . format(args.input)
            raise Exception(msg)
    else:
        scan_results_file = args.input

    output_root_dir = None
    if args.output is None or args.output == '' or args.output == '.':
        output_root_dir = "./build"
    else:
        output_root_dir = remove_ending_slashes(args.output)
    if os.path.isfile(output_root_dir):
        msg = 'Output "{}" already exists and it is a file.' . format(output_root_dir)
        raise Exception
    if not os.path.isdir(output_root_dir):
        os.makedirs(output_root_dir)
    
    f = open(scan_results_file, 'rt')
    created = []
    updated = []
    deleted = []
    for s in f:
        s = s.strip()
        s = remove_comment(s, COMMENT_SYMBOL)
        if len(s) == 0:
            continue
        parts = s.split("\t")
        #print(s, parts)
        if len(parts) < 2:
            continue
        if parts[0] == 'created':
            created.append(parts[1])
        elif parts[0] == 'updated':
            updated.append(parts[1])
        elif parts[0] == 'deleted':
            deleted.append(parts[1])
    f.close()

    '''created.append('/tmp/123/')
    created.append('testdir1/NewFile.txt')
    created.append('c:\\temp/NewFileOnWindows.txt')
    deleted.append('/tmp/FileForDelete_on_unix.txt')
    deleted.append('c:\\temp\\FileForDelete_on_windows.txt')
    deleted.append('c:\\temp\\dir1\\')'''

    if DEBUG_MODE: print('CREATED:', created)
    if DEBUG_MODE: print('UPDATED:', updated)
    if DEBUG_MODE: print('DELETED:', deleted)

    filename_unix = PREFIX_BUILD + '_' + get_timestamp(None, '-', '_', '-') + '_unix.sh'
    filename_windows = PREFIX_BUILD + '_' + get_timestamp(None, '-', '_', '-') + 'windows.bat'
    filename_unix = os.path.join(output_root_dir, filename_unix)
    filename_windows = os.path.join(output_root_dir, filename_windows)

    fu = open(filename_unix, 'wt', encoding='utf-8', newline='\n')
    fu.write('#!/usr/bin/env sh\n')
    fu.write('\n')

    fw = open(filename_windows, 'wt', encoding='utf-8', newline='\r\n')
    fw.write('echo off\n')
    fw.write('cls\n')
    fw.write('\n')

    if defined(args.note):
        # комментарий к выполняемому действию
        fu.write('# ' + args.note + '\n')
        fu.write('\n')
        fw.write('rem ' + args.note + '\n')
        fw.write('\n')

    do_build__delete(output_root_dir, fu, fw, deleted)
    do_build__create(output_root_dir, fu, fw, created)
    do_build__update(output_root_dir, fu, fw, updated)

    fu.close()
    fw.close()


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
            # параметров в командной строке не задано - вывести справку и выйти
            parser.print_help()
            exit(0)
        args = parser.parse_args()

    args = prepare_arguments(args)
    if DEBUG_MODE: print("args:", args); #exit(0)

    if args.command == 'help':
        parser.print_help()
    elif args.command == 'scan':
        #print("output:", args.output)
        #print("dirs[]:", args.directory)
        f = get_output(args.output, args.command, args.append, args.note)
        #print('output:', f)
        skip = get_skipping_items(args)
        for d in args.directory:
            do_scan(d, f, args, skip, INITIAL_DEPTH)
        close_output(f, args.command)
    elif args.command == 'compare':
        do_compare(args)
    elif args.command == 'build':
        do_build(args)
