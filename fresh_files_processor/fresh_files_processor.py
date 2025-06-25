#!/usr/bin/python3

import sys
import os
#import glob
import fnmatch
from pprint import pprint
import datetime

#----- Из строки вида key=value выделить ключ и значение (возможно, убрать пробелы/табуляции) -----
def split_key_value(
        s,
        sep = "=",
        multiseps_as_one = False,
        strip_spaces_in_key = True,
        strip_spaces_in_value_begin = False,
        strip_spaces_in_value_end = False
):
    key, value = None, None
    p = s.find(sep)
    #print(p)
    if p > 0:
        key = s[0:p]
        if strip_spaces_in_key:
            key = key.strip()
        value = s[p+1:len(s)]
        if multiseps_as_one:
            # множественные символы-разделители воспринимать как один
            while len(value) > 0 and value.startswith(sep):
                value = value[len(sep): len(value)]
        if strip_spaces_in_value_begin:
            value = value.lstrip()
        if strip_spaces_in_value_end:
            value = value.rstrip()
    return key, value

#s = "  \tparam1 =====\tvalue ";    key, value = split_key_value(s, sep="=", multiseps_as_one=True, strip_spaces_in_value_begin=True, strip_spaces_in_value_end=True)
#print("s='{}'  key='{}'  value='{}'" . format(s, key, value))
#exit(0)

def read_config(config_path):
    config = {
        "dir": [],              # каталоги, из которых получить список файлов для последующей обработки
        "mask": [],             # маски выбираемых файлов
        "processed": None,      # файл со списком обработанных ранее файлов, чтобы к ним больше не применять обработку
        "sort_by": None,        # критерий сортировки списка файлов
        "sort_reverse": False,  # сортировать в обратном порядке

        "commands": []          # список команд применяемых к файлам
    }
    
    with open(config_path, "rt") as f:
        reading_commands_now = False
        for s in f:
            s = s.strip()
            if len(s) == 0:
                continue
            if s[0] == "#":
                continue # комментарий
            if s == "<commands>":
                # начался блок с командами операционной системы
                reading_commands_now = True
                continue
            if s == "</commands>":
                # закончился блок с командами операционной системы
                reading_commands_now = False
                continue
            if not reading_commands_now:
                key, value = split_key_value(s, sep="=", strip_spaces_in_key=True, strip_spaces_in_value_begin=True, strip_spaces_in_value_end=True)
                #print(s, key, value)
                if key == "dir":
                    config["dir"].append(value)
                elif key == "mask":
                    config["mask"].append(value)
                elif key == "processed":
                    config["processed"] = value
                elif key in ["sort_by", "sort-by"]:
                    config["sort_by"] = value
                elif key in ["sort_reverse", "sort-reverse"]:
                    value = value.lower()
                    if value in ["yes", "true", "1", "on"]:
                        value = True
                    elif value in ["no", "false", "0", "off"]:
                        value = False
                    else:
                        continue
                    config["sort_reverse"] = value
                else:
                    print("WARNING! Unprocessable key '{}' with value '{}'" . format(key, value))
            if reading_commands_now:
                config["commands"].append(s)
    return config


def get_files_list(dirname, files_masks):
    found = []
    if os.path.isdir(dirname):
        items = os.listdir(dirname)
        #print("items:", items)
        for one_item in items:
            path = os.path.join(dirname, one_item)
            if os.path.isdir(path):
                continue
            if len(files_masks) > 0:
                matched = False
                for one_mask in files_masks:
                    ok = fnmatch.fnmatch(one_item, one_mask)
                    if ok:
                        matched = True
                        break # если совпадение имени файла с одной из масок, то остальные маски можно не проверять
                if not matched:
                    # имя текущего файла не совпало ни с одной допустимой маской файлов
                    #print("skip:", one_item)
                    continue
            elem = {
                "shortname": one_item,
                "longname": path,
                "filesize": os.path.getsize(path),
                "ctime": os.path.getctime(path),
                "mtime": os.path.getmtime(path),
                "atime": os.path.getatime(path),
                "filetime": datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
            }

            found.append(elem)
            #found.append(path)
    return found


def file_to_array(filename):
    result = []
    if filename == None:
        return result
    if len(filename) == None:
        return result
    if not os.path.isfile(filename):
        return result
    with open(filename, "rt") as f:
        for s in f:
            s = s.strip()
            if len(s) == 0:
                continue
            if s[0] == "#":
                continue
            result.append(s)
    return result


def process_config(config_path):
    if not os.path.isfile(config_path):
        print("File {} not found." . format(config_path))
        return False
    config = read_config(config_path)
    print("--- config: ---"); pprint(config); print("--- end of config ---")
    files_list = []
    for elem in config["dir"]:
        files_list += get_files_list(elem, config["mask"])
    if config["sort_by"] != None:
        # newlist = sorted(list_to_be_sorted, key=lambda d: d['name'])
        print("SortBy:", config["sort_by"], "   reverse=", config["sort_reverse"], sep="")
        files_list = sorted(files_list, key=lambda d: d[config["sort_by"]], reverse=config["sort_reverse"])
    #print("--- files_list: ---"); pprint(files_list); print("... end of files_list ...")
    processed_list = file_to_array(config["processed"])
    #print("processed_list:", processed_list)

    f_processed = None
    if config["processed"] != None and len(config["processed"]) > 0:
        f_processed = open(config["processed"], "at")
    for one_file_dict in files_list:
        if one_file_dict["longname"] in processed_list:
            # файл уже обрабатывался ранее
            print("skip file '{}' because it was processed earlier" . format(one_file_dict["longname"]))
            continue
        print(one_file_dict)
        for one_cmd in config["commands"]:
            for key in one_file_dict.keys():
                if type(one_file_dict[key]) != type("abc"):
                    one_file_dict[key] = str(one_file_dict[key])
                one_cmd = one_cmd.replace("${" + key + "}", one_file_dict[key])
            print("CMD:", one_cmd)
            os.system(one_cmd)
        
        if f_processed != None:
            f_processed.write(one_file_dict["longname"] + "\n")
    if f_processed != None:
        f_processed.close()
    return True


if __name__ == "__main__":
    process_config("config1.cfg"); exit(0)
    for i in range(1, len(sys.argv)):
        process_config(sys.argv[i])
    