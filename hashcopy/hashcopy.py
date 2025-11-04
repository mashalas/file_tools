#!/usr/bin/env python3

import argparse
import sys
import os
import hashlib
import zlib
import shutil
import fnmatch
#import glob

HASH_METHODS = ['crc32', 'md5', 'sha256', 'sha512', 'sha384', 'sha1']
HASH_OPEN_DELIMITER = "["
HASH_CLOSE_DELIMITER = "]"

_DEBUG_ARGS = []
#_DEBUG_ARGS = ["--name", "--pattern", "*.txt", "-m", "./dir1"]
#_DEBUG_ARGS = ["--name", "--pattern", "*.txt", "-r", "./dir1"]
#_DEBUG_ARGS = ["--name", "--pattern", "*.txt", "-r", "./dir1", "newdir"]


#----- Разделить путь к файлу на каталог, имя без расширения и расширение -----
# (расширение - последние символы начиная с последней точки)
def split_filename_to_dir_name_extension(path):
    last_dot_position = -1
    last_slash_position = -1
    for i in range(len(path)-1, -1, -1):
        #print(i, path[i])
        ch = path[i]
        if ch == "/" or ch == "\\":
            last_slash_position = i
            break
        if ch == "." and last_dot_position < 0:
            last_dot_position = i
    if last_dot_position < 0:
        last_dot_position = len(path)
    dir = ''
    name = ''
    extension = ''
    if last_slash_position >= 0:
        dir = path[0:last_slash_position+1]
    name = path[len(dir):last_dot_position]
    extension = path[last_dot_position:len(path)]
    return dir, name, extension

#print(split_filename_to_dir_name_extension("c:\\temp\\file1.2025.txt")); exit(0)
#print(split_filename_to_dir_name_extension("c:\\temp\\file1.txt")); exit(0)
#print(split_filename_to_dir_name_extension("c:\\temp\\file1")); exit(0)
#print(split_filename_to_dir_name_extension("file.zip")); exit(0)
#print(split_filename_to_dir_name_extension("/tmp/file.zip")); exit(0)
#print(split_filename_to_dir_name_extension("/file.zip")); exit(0)
#print(split_filename_to_dir_name_extension("qwe")); exit(0)


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
        result = ''
    return result


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
        result = ''
    return result


def get_hash(filename, method = HASH_METHODS[0]):
    result = ""
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


# ----- Из строки s удалить перечисленные в removing_symbols символы находящиеся в начале строки s ---
def remove_leading_symbols(s, removing_symbols):
    while len(s) > 0 and s[0] in removing_symbols:
        s = s[1:len(s)]
    return s


# ----- Из строки s удалить перечисленные в removing_symbols символы находящиеся в конце строки s ---
def remove_ending_symbols(s, removing_symbols):
    while len(s) > 0 and s[-1] in removing_symbols:
        s = s[0:len(s)-1]
    return s

#print(remove_ending_symbols("abc,.,", ",.?")); exit(0)
#print(remove_leading_symbols(",,-,abc,.,", ",.?")); exit(0)


def build_dst_file_name(src_file_name, dst_dir, algo:str, print_algo_name:bool):
    if not os.path.isfile(src_file_name):
        return None
    hash = get_hash(src_file_name, algo)
    src_dir, src_name, src_extension = split_filename_to_dir_name_extension(src_file_name)
    if dst_dir is None or dst_dir == '':
        # целевой каталог не указан - файл остаётся в исходном каталоге
        dst_dir = remove_ending_symbols(src_dir, '\\/')
    if print_algo_name:
        # перед хешем поставить имя алгоритма
        algo_name = algo + '='
    else:
        # имя алгоритма не писать, только сам хеш
        algo_name = ''
    target_file_name = src_name + \
        HASH_OPEN_DELIMITER + algo_name + hash + HASH_CLOSE_DELIMITER + \
        src_extension
    result = os.path.join(dst_dir, target_file_name)
    return result


def hashcopy(src, dst, args):
    #print(src, dst)
    if not dst is None:
        if not os.path.exists(dst):
            os.makedirs(dst)
        elif os.path.isfile(dst):
            msg = 'Destination "{}" already exists and it is not directory' . format(dst)
            raise Exception(msg)
    if os.path.isdir(src):
        # источник - каталог
        items = os.listdir(src)
        #print(items)
        for one_item in items:
            path = os.path.join(src, one_item)
            if os.path.isfile(path):
                if args.pattern != None:
                    # указан шаблон имён файлов
                    if not fnmatch.fnmatch(one_item, args.pattern):
                        # нет совпадения с шаблоном
                        continue
                # либо шаблон не указан и обрабатываются все файлы, либо совпадение с шаблоном
                hashcopy(path, dst, args)
            elif args.recursive and os.path.isdir(path):
                dst_next = dst
                if not dst_next is None:
                    dst_next = os.path.join(dst_next, one_item)
                hashcopy(path, dst_next, args)
    elif os.path.isfile(src):
        # источник - файл
        dst_file_name = build_dst_file_name(src, dst, args.algo, args.name)
        if args.move:
            os.rename(src, dst_file_name)
        else:
            shutil.copyfile(src, dst_file_name, follow_symlinks=True)
            shutil.copystat(src, dst_file_name, follow_symlinks=True) # скопировать мета-информацию о файле (время правки и т.д.)
    else:
        print('Source "{}" not exists' . format(src))


def get_arg_parser_definiton():
    parser = argparse.ArgumentParser(
        prog = 'hashcopy',
        description = '''Копирование (перемещение при использовании параметра -m|--move) файлов с добавлением к имени контрольной суммы копируемого файла
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-a', '--algo', default=HASH_METHODS[0], help='Алгоритм вычисления контрольных сумм. По умолчанию: ' + HASH_METHODS[0] + '; возможные варианты: ' + ', '.join(HASH_METHODS))
    parser.add_argument('-n', '--name', action='store_true', help='Помещать перед хешем имя алгоритма хеширования')
    parser.add_argument('-m', '--move', action='store_true', help='Перемещать файлы, а не копировать')
    parser.add_argument('-r', '--recursive', action='store_true', help='рекурсивный обход каталогов')
    parser.add_argument('-p', '--pattern', help='если в качестве источника указан каталог, в этом параметре можно задать маску файлов с использованием символов подстановки "*" и "?"')

    parser.add_argument('src', nargs=1, help='Исходный файл, каталог или маска файлов в каталоге')
    parser.add_argument('dst', nargs='?', help='Целевой файл или каталог')

    return parser


if __name__ == "__main__":
    parser = get_arg_parser_definiton()
    if len(_DEBUG_ARGS) > 0:
        # использовать отладочные параметры
        args = parser.parse_args(_DEBUG_ARGS)
    else:
        # использовать реальные параметры командной строки
        args = parser.parse_args()
    #print("args:", args); #exit(0)
    hashcopy(args.src[0], args.dst, args)
