#!/usr/bin/python3

import os
import sys
import hashlib
from pprint import pprint

diffs_count = 0

def help():
    print("compare_dirs.py [options] <dir1> <dir2>")
    print("Compare contents of two directories.")
    print("Options:")
    print("  -s --size         compare files by sizes")
    print("  -t --time         compare files by modification times")
    print("  -d --data         compare files by its content")
    print("  --skip <item>     do not compare specified item (directory or file)")

def argparse(argv):
    params = {}
    params["size"] = False
    params["time"] = False
    params["data"] = False
    params["help"] = False
    params["skip"] = []
    params["dir1"] = None
    params["dir2"] = None
    i = 0
    while i < len(argv)-1:
        i += 1
        a = argv[i]
        #print(a)
        if a == "-h" or a == "--help" or a == "-help" or a == "/?":
            params["help"] = True
        if a == "-s" or a == "--size":
            params["size"] = True
            continue
        if a == "-t" or a == "--time":
            params["time"] = True
            continue
        if a == "-d" or a == "--data":
            params["data"] = True
            continue
        if a == "--skip":
            i += 1
            params["skip"].append(argv[i])
            continue
        if params["dir1"] == None:
            params["dir1"] = a
            continue
        if params["dir2"] == None:
            params["dir2"] = a
            continue
        continue
    if params["dir1"] == None:
        params["help"] = True
    if params["dir2"] == None:
        params["help"] = True
    return params


# -------- Расчёт контрольной суммы для файла --------
def get_file_hash(filename, block_size = 2**20):
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


def do_compare(dir1, dir2, params, level = 0):
    global diffs_count
    if level == 0:
        print("--- compare [{}] and [{}] ---" . format(dir1, dir2))
    space = ""
    for i in range(level):
        space += "  "
    #print("enter to {} and {}" . format(dir1, dir2))

    if not os.path.isdir(dir1):
        print(space, "Directory [{}] does not exist." . format(dir1))
        return False
    if not os.path.isdir(dir2):
        print(space, "Directory [{}] does not exist." . format(dir2))
        return False


    errors_found = False
    try:
        dir1items = os.listdir(dir1)
    except:
        errors_found = True
        print(space, "Cannot read contents for [{}]" . format(dir1))
    try:
        dir2items = os.listdir(dir2)
    except:
        errors_found = True
        print(space, "Cannot read contents for [{}]" . format(dir2))
    if errors_found:
        return False

    bothitems = dir1items + dir2items
    bothitems = list(set(bothitems))
    #print(dir1items); print(dir2items)
    dir1items.sort()
    dir2items.sort()
    bothitems.sort()
    #print(dir1items); print(dir2items); print(bothitems); exit(0)

    for item in bothitems:
        if item in params["skip"]:
            # не сравнивать объект с таким именем
            continue
        path1 = os.path.join(dir1, item)
        path2 = os.path.join(dir2, item)
        #print("q1", path1, path2)
        if os.path.exists(path1) and os.path.exists(path2):
            # объект существует в обоих каталогах
            if os.path.isdir(path1):
                path1kind = "d"
            elif os.path.isfile(path1):
                path1kind = "f"
            else:
                path1kind = "?"

            if os.path.isdir(path2):
                path2kind = "d"
            elif os.path.isfile(path2):
                path2kind = "f"
            else:
                path2kind = "?"

            if path1kind != path2kind:
                # объекты различаются типом
                diffs_count += 1
                #print(space, '"{}" is "{}" but "{}" is "{}"' . format(path1, path1kind, path2, path2kind))
                print(str(diffs_count) + ") reason: are differ by kind")
                print("  ", path1kind, path1)
                print("  ", path2kind, path2)
                print()
                continue
            # объекты одного типа (файл или каталог)
            if path1kind == "d" and path2kind == "d":
                # каталоги
                do_compare(path1, path2, params, level+1)
            if path1kind == "f" and path2kind =="f":
                # файлы
                #diff_size = False
                #diff_time = False
                #diff_data = False
                diffs_list = []

                if params["size"]:
                    # сравнить размеры файлов
                    size1 = os.path.getsize(path1)
                    size2 = os.path.getsize(path2)
                    if size1 != size2:
                        diffs_list.append("size")
                if params["time"]:
                    # сравнить время модификации файлов
                    time1 = os.path.getmtime(path1)
                    time2 = os.path.getmtime(path2)
                    if time1 != time2:
                        diffs_list.append("time")
                if params["data"]:
                    # сравнить содержимое файлов
                    hash1 = get_file_hash(path1)
                    hash2 = get_file_hash(path2)
                    if hash1 != hash2:
                        diffs_list.append("data")

                if len(diffs_list) > 0:
                    # есть различие в файлах
                    diffs_count += 1
                    #print(space, '"{}" and "{}" are differ by:' . format(path1, path2), ", ".join(diffs_list))
                    print(str(diffs_count) + ") reason: are differ by", ", ".join(diffs_list))
                    print("  " + path1)
                    print("  " + path2)
                    print()

        else:
            # объект существует только в одном каталоге
            path1exists = os.path.exists(path1)
            path2exists = os.path.exists(path2)
            diffs_count += 1
            print(str(diffs_count) + ") reason: exists/not exists")
            if path1exists:
                #print(space, '"{}" exists but "{}" not exists' . format(path1, path2))
                print("  exists:     " + path1)
                print("  not exists: " + path2)
            if path2exists:
                #print(space, '"{}" exists but "{}" not exists' . format(path2, path1))
                print("  exists:     " + path2)
                print("  not exists: " + path1)
            print()
            #print(path1, path2)

    if level == 0:
        print("Differences found: {}." . format(diffs_count))
    return True


if __name__ == "__main__":
    params = argparse(sys.argv)
    #pprint(params)
    if params["help"]:
        help()
    else:
        do_compare(params["dir1"], params["dir2"], params)
