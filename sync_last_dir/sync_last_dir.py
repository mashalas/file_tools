
import argparse
#import sys
import os
import zlib
import hashlib
import datetime
import shutil
from pprint import pprint

MESSAGE_KIND__INFO = "i"
MESSAGE_KIND__WARNING = "w"
MESSAGE_KIND__ERROR = "e"
MESSAGE_KIND__FATAL = "f"
MESSAGE_KIND__RAW = "r"

SORT_BY__NAME = "name"
SORT_BY__DATE = "date"

BACKUP_EXTENSION = ".bkp"

global_VerboseMode = False



def print_message(kind, msg):
    if kind != MESSAGE_KIND__RAW:
        if msg[-1] not in [".", "!", "?"]:
            msg += "."
    if kind == MESSAGE_KIND__FATAL:
        raise Exception(msg)
    elif kind == MESSAGE_KIND__ERROR:
        msg = "ERROR!!! " + msg
    elif kind == MESSAGE_KIND__WARNING:
        msg = "WARNING! " + msg
    elif kind == MESSAGE_KIND__INFO:
        global global_VerboseMode
        if not global_VerboseMode:
            return
        msg = "INFO. " + msg
    print(msg)


# ----- Дополнить строку до необходимой длины добавив в конце пробелы -----
def set_string_length(s, target_length = 10):
    #0x804483c1
    #0123456789
    while len(s) < target_length:
        s += " "
    return s

# ----- Расчёт контрольной суммы для файла по алгоритму crc32 -----
def get_file_crc32(filename):
    if not os.path.isfile(filename):
        return ""
    crc32_hex = ""
    try:
        with open(filename, "rb") as f:
            data = f.read()
            crc32_dec = zlib.crc32(data)
            crc32_hex = hex(crc32_dec)
            crc32_hex = set_string_length(crc32_hex, 10)
    except:
        crc32_hex = "Cannot read file"
        while len(crc32_hex) < 10:
            crc32_hex += "_"
    return crc32_hex


# ----- Расчёт контрольной суммы для файла по алгоритму md5 -----
def get_file_md5(filename, block_size = 2**20):
    Result = ""
    if not os.path.isfile(filename):
        return Result
    md5 = hashlib.md5()
    try:
        f = open(filename, "rb")
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        Result = md5.hexdigest()
    except:
        Result = "Cannot read file"
        while len(Result) < 32:
            Result += "_"
    return Result


# ----- Является ли переданный путь резервной копией другого пути -----
def is_backup(path):
    if path.endswith("}" + BACKUP_EXTENSION):
        return True # переданный путь уже сам является резервной копией
    return False


# ----- file1.txt => file1.txt{12345-67890abc}.bkp {размер в байтах - контрольная сумма crc32} -----
# ----- dir1 => dir1{removed_YYYY-MM-DD_HH-MM-SS}.bkp
def get_backup_path(path) -> str:
    if is_backup(path):
        return ""
    backup_name = ""
    if os.path.isdir(path):
        # каталог
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") # https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        backup_name = path + "{" + timestamp + "}" + BACKUP_EXTENSION 
        pass
    elif os.path.isfile(path):
        # файл
        size_int = os.path.getsize(path)
        size_str = str(size_int)
        crc32 = get_file_crc32(path)
        backup_name = path + "{" + size_str + "-" + crc32 + "}" + BACKUP_EXTENSION
    if backup_name != "" and os.path.exists(backup_name):
        # если уже существует такая резервная копия, то новую не создавать
        backup_name = ""
    return backup_name


def define_arguments():
    # --- Создание объекта ---
    parser = argparse.ArgumentParser(description="Синхронизация содержимого каталогов")

    # --- именованные параметры ---
    parser.add_argument("-s", "--sort-by", help="Сортировать список каталогов для выбора последнего по дате (d, date) или имени (n, name). По умолчанию - по дате.", default="date", choices=["d", SORT_BY__DATE, "n", SORT_BY__NAME])
    parser.add_argument("-r", "--recursive", help="Рекурсивно с подкаталогами", action="store_true")
    parser.add_argument("-v", "--verbose", help="Выводить подробную информацию о выполняемых действиях", action="store_true")
    parser.add_argument("-b", "--backups", help="Создавать резервные копии удаляемых или перезаписываемых файлов", action="store_true")
    parser.add_argument("-D", "--no-delete", help="Не удалять из целевого каталога", action="store_true")
    parser.add_argument("-U", "--no-update", help="Не заменять в целевом каталоге", action="store_true")
    parser.add_argument("-C", "--no-create", help="Не создавать в целевом каталоге", action="store_true")

    # --- позиционные параметры ---
    # *  аргументы могут быть не заданы
    # +  хотя бы один аргумент должен быть передан
    parser.add_argument("dirs", help="Синхронизируемые каталоги", nargs=2)

    return parser


def do_sync_one(src_path, dst_path, args, can_copy_dir:bool = False):
    if is_backup(src_path):
        return
    if is_backup(dst_path):
        return
    
    dst_backup = ""
    if args.backups:
        dst_backup = get_backup_path(dst_path)
        if os.path.exists(dst_backup):
            dst_backup = ""

    if os.path.isfile(src_path):
        # +++++ исходный объект - файл +++++
        if os.path.isdir(dst_path):
            # +++ целевой объект - каталог +++
            if args.no_delete:
                return
            if dst_backup != "":
                os.rename(dst_path, dst_backup)
            else:
                os.rmtree(dst_path)
            print_message(MESSAGE_KIND__INFO, "Replace directory by file [{}] => [{}]" . format(src_path, dst_path))
            shutil.copyfile(src_path, dst_path, follow_symlinks=True)
            shutil.copystat(src_path, dst_path, follow_symlinks=True) # скопировать мета-информацию о файле (время правки и т.д.)
        elif os.path.isfile(dst_path):
            # +++ целевой объект - тоже файл +++
            if args.no_update:
                return # запрещено заменять объекты одного типа
            files_are_diff = False
            src_size = os.path.getsize(src_path)
            dst_size = os.path.getsize(dst_path)
            if src_size != dst_size:
                # файлы различаются по размеру
                files_are_diff = True
                #print_message(MESSAGE_KIND__INFO, "Size of [{}]={} <> size of [{}]={}" . format(src_path, src_size, dst_path, dst_size))
            else:
                # файлы одинакового размера, проверить по контрольной суме
                src_hash = get_file_md5(src_path)
                dst_hash = get_file_md5(dst_path)
                if src_hash != dst_hash:
                    # файлы различаются по контрольным суммам
                    files_are_diff = True
                    #print_message(MESSAGE_KIND__INFO, "Hash of [{}]={} <> hash of [{}]={}" . format(src_path, src_hash, dst_path, dst_hash))
            if files_are_diff:
                if dst_backup != "":
                    os.rename(dst_path, dst_backup)
                else:
                    os.remove(dst_path)
                print_message(MESSAGE_KIND__INFO, "Update [{}] => [{}]" . format(src_path, dst_path))
                shutil.copyfile(src_path, dst_path, follow_symlinks=True)
                shutil.copystat(src_path, dst_path, follow_symlinks=True) # скопировать мета-информацию о файле (время правки и т.д.)
        elif not os.path.exists(dst_path):
            # +++ целевой объект не существует +++
            if args.no_create:
                return # запрещено создавать в целевом каталоге
            print_message(MESSAGE_KIND__INFO, "Create [{}] => [{}]" . format(src_path, dst_path))
            #shutil.copy(src_path, dst_path, follow_symlinks=True) 
            shutil.copyfile(src_path, dst_path, follow_symlinks=True)
            shutil.copystat(src_path, dst_path, follow_symlinks=True) # скопировать мета-информацию о файле (время правки и т.д.)         
    elif os.path.isdir(src_path):
        # +++++ исходный объект - каталог +++++
        if os.path.isfile(dst_path):
            # +++ целевой объект - файл +++
            if args.no_delete:
                return
            if dst_backup != "":
                os.rename(dst_path, dst_backup)
            else:
                os.remove(dst_path)
            if can_copy_dir:
                print_message(MESSAGE_KIND__INFO, "Create directory [{}]" . format(dst_path))
                shutil.copytree(src_path, dst_path)
            #else:
            #    os.mkdir(dst_path)
    elif not os.path.exists(src_path) and os.path.exists(dst_path):
        # +++++ исходный объект не сущестует, но в целевом каталоге есть объект +++++
        if args.no_delete:
            return
        print_message(MESSAGE_KIND__INFO, "Delete [{}]" . format(dst_path))
        if dst_backup != "":
            os.rename(dst_path, dst_backup)
        else:
            if os.path.isdir(dst_path):
                os.rmtree(dst_path)
            else:
                os.remove(dst_path)
            


def get_last_dir(dirname, sort_by):
    items = os.listdir(dirname)
    #inner_dirs = []
    last_dir_name = ""
    last_dir_time = None
    for elem in items:
        path = os.path.join(dirname, elem)
        if not os.path.isdir(path):
            continue
        if sort_by == SORT_BY__NAME:
            if last_dir_name == "" or elem > last_dir_name:
                last_dir_name = elem
        elif sort_by == SORT_BY__DATE:
            dir_time = os.path.getmtime(path)
            if last_dir_time == None or dir_time > last_dir_time:
                last_dir_name = elem
                last_dir_time = dir_time
    return last_dir_name


def do_sync(src_dir, dst_dir, args, depth = 0):
    if args.verbose and depth == 0:
        print_message(MESSAGE_KIND__INFO, "Sync [{}] and [{}]" . format(src_dir, dst_dir))
    if not os.path.isdir(src_dir):
        print_message(MESSAGE_KIND__ERROR, "Source [{}] is not directory" . format(src_dir))
    if os.path.isfile(dst_dir):
        print_message(MESSAGE_KIND__ERROR, "Target [{}] is file" . format(dst_dir))
    if not os.path.exists(dst_dir):
        os.mkdir(dst_dir)

    src_items = os.listdir(src_dir)
    dst_items = os.listdir(dst_dir)
    src_items_set = set(src_items)
    #print("src:", src_items, "  dst:", dst_items); return

    # +++++ синхронизация файлов +++++
    # +++ удалить в целевом каталоге объекты, которых нет в исходном +++
    for elem in dst_items:
        if not elem in src_items_set:
            # elem присутствует в целевом каталоге, но отсутствует в исходном
            src_path = os.path.join(src_dir, elem)
            dst_path = os.path.join(dst_dir, elem)
            do_sync_one(src_path, dst_path, args)
    # +++ скопировать отсутствующие в целевом каталоге файлы +++
    for elem in src_items:
        src_path = os.path.join(src_dir, elem)
        if os.path.isfile(src_path):
            dst_path = os.path.join(dst_dir, elem)
            do_sync_one(src_path, dst_path, args)

    # +++++ синхронизация каталогов (переход на уровень вглубь) +++++
    if args.recursive:
        for elem in src_items:
            src_path = os.path.join(src_dir, elem)
            if os.path.isdir(src_path):
                dst_path = os.path.join(dst_dir, elem)
                #do_sync_one(src_path, dst_path, args) # чтобы удалить файл в целевом, когда в исходнмо это каталог
                do_sync(src_path, dst_path, args, depth+1)
    return


def prepare_args_for_debug(args):
    args.dirs.append("G:\\sources\\python\\file_tools\\sync_last_dir\\dir1")
    args.dirs.append("G:\\sources\\python\\file_tools\\sync_last_dir\\dir2")
    args.backups = True
    pass

if __name__ == "__main__":
    parser = define_arguments()
    args = parser.parse_args()
    #prepare_args_for_debug(args)
    pprint(args)
    global_VerboseMode = args.verbose

    if len(args.dirs) < 2:
        print("Should be specified two or more directories")
        exit(1)
    if not os.path.isdir(args.dirs[0]):
        print("Source directory [{}] does not exist" . format(args.dirs[0]))
        exit(2)
    last_inner_dir = get_last_dir(args.dirs[0], args.sort_by)
    print_message(MESSAGE_KIND__INFO, "last_inner_dir: " + last_inner_dir)
    if last_inner_dir == "":
        print_message(MESSAGE_KIND__WARNING, "Source directory [{}] does not contain subdirectories" . format(args.dirs[0]))
        exit(0) # каталог не содержит подкаталогов
    last_inner_path = os.path.join(args.dirs[0], last_inner_dir)
    print_message(MESSAGE_KIND__INFO, "last_inner_path: " + last_inner_path)

    for i in range(1, len(args.dirs)):
        if not os.path.exists(args.dirs[i]):
            os.mkdir(args.dirs[i])
        do_sync(last_inner_path, os.path.join(args.dirs[i], last_inner_dir), args)
