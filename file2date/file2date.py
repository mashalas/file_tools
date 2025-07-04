
import os
import sys
import datetime
import shutil
import fnmatch


SUBDIRS_STRUCTURE = {
    "year": True,
    "month": True,
    "day": True,
    "hour": False,
    "minute": False,
    "second": False
}

PRINT_COPIED = True
PRINT_SKIPPED = True

def help():
    print("file2data.py <dst_root_dir> <src_file_or_dir> [mask]")


def file2date(dst_root_dir, src_file_or_dir, mask = None):
    if os.path.isdir(src_file_or_dir):
        # указан каталог, из которого нужно скопировать файлы
        items = os.listdir(src_file_or_dir)
        for one_item in items:
            path = os.path.join(src_file_or_dir, one_item)
            if os.path.isdir(path):
                continue
            if mask != None and len(mask) > 0:
                if not fnmatch.fnmatch(one_item, mask):
                    continue # файл не соответствует маске
            file2date(dst_root_dir, path)

    elif os.path.isfile(src_file_or_dir):
        # указан один конкретный файл
        short_filename = os.path.basename(src_file_or_dir)
        mtime = os.path.getmtime(src_file_or_dir)
        mtime_datetime = datetime.datetime.fromtimestamp(mtime)
        
        dst_dir = dst_root_dir
        if SUBDIRS_STRUCTURE["year"]:
            dst_dir = os.path.join(dst_dir, mtime_datetime.strftime("%Y"))
        if SUBDIRS_STRUCTURE["month"]:
            dst_dir = os.path.join(dst_dir, mtime_datetime.strftime("%m"))
        if SUBDIRS_STRUCTURE["day"]:
            dst_dir = os.path.join(dst_dir, mtime_datetime.strftime("%d"))
        if SUBDIRS_STRUCTURE["hour"]:
            dst_dir = os.path.join(dst_dir, mtime_datetime.strftime("%H"))
        if SUBDIRS_STRUCTURE["minute"]:
            dst_dir = os.path.join(dst_dir, mtime_datetime.strftime("%M"))
        if SUBDIRS_STRUCTURE["second"]:
            dst_dir = os.path.join(dst_dir, mtime_datetime.strftime("%S"))

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        dst_filename = os.path.join(dst_dir, short_filename)
        if not os.path.exists(dst_filename):
            if PRINT_COPIED:
                print('copy "{}" => "{}"' . format(src_file_or_dir, dst_filename))
            shutil.copy2(src_file_or_dir, dst_filename) # copy - копирование с сохранением метаинформации (дата изменения файла)
        else:
            if PRINT_SKIPPED:
                print('"{}" already exists' . format(dst_filename))
    else:
        # не существует исходный файл или каталог
        print('WARNING! Source file or directory "{}" does not exist.' . format(src_file_or_dir))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help", "/?", "/help", "-help"):
        help()
        exit(0)
    dst_root_dir = sys.argv[1]
    src_file_or_dir = sys.argv[2]
    mask = None
    if len(sys.argv) >= 4:
        mask = sys.argv[3]
    file2date(dst_root_dir, src_file_or_dir, mask)
