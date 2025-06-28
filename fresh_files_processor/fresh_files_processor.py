#!/usr/bin/python3

import sys
import os
import fnmatch
from pprint import pprint
import datetime


class FFPConfig():
    def __init__(self, filename) -> None:
        STATE__NOT_COMMANDS = "not_commands"
        STATE__PRIOR_COMMANDS = "prior_commands"
        STATE__COMMANDS = "commands"
        STATE__POST_COMMANDS = "post_commands"
        state = STATE__NOT_COMMANDS
        
        self._filename = filename
        self.dir = []
        self.mask = []
        self.processed = None
        self.sort_by = None
        self.sort_reverse = False
        self.prior_commands = []
        self.commands = []
        self.post_commands = []
        self.only_newer = None
        self.skip_newer = None
        self.min_age = None
        self.max_age = None
        with open(filename, "rt") as f:
            #reading_commands_now = False
            for s in f:
                s = s.strip()
                if len(s) == 0:
                    continue
                if s[0] == "#":
                    continue # комментарий
                if s == "<prior_commands>":
                    # начался блок с командами операционной системы выполняемыми до начала обработки файлов
                    state = STATE__PRIOR_COMMANDS
                    continue
                if s == "<commands>":
                    # начался блок с командами операционной системы обработки файлов
                    state = STATE__COMMANDS
                    continue
                if s == "<post_commands>":
                    # начался блок с командами операционной системы выполняемым после обработки файлов
                    state = STATE__POST_COMMANDS
                    continue
                if s in ["</commands>", "</prior_commands>", "</post_commands>"]:
                    # закончился блок с командами операционной системы
                    state = STATE__NOT_COMMANDS
                    continue
                
                if state == STATE__NOT_COMMANDS:
                    key, value = split_key_value(s, sep="=", strip_spaces_in_key=True, strip_spaces_in_value_begin=True, strip_spaces_in_value_end=True)
                    #print(s, key, value)
                    if key == "dir":
                        self.dir.append(value)
                    elif key == "mask":
                        self.mask.append(value)
                    elif key == "processed":
                        self.processed = value
                    elif key in ["sort_by", "sort-by"]:
                        self.sort_by = value
                    elif key in ["sort_reverse", "sort-reverse"]:
                        value = value.lower()
                        if value in ["yes", "true", "1", "on"]:
                            self.sort_reverse = True
                        elif value in ["no", "false", "0", "off"]:
                            self.sort_reverse = False
                    elif key == "only_newer":
                        self.only_newer = get_date_time_from_string(value)
                    elif key == "skip_newer":
                        self.skip_newer = get_date_time_from_string(value)
                    elif key == "min_age":
                        self.min_age = get_age(value)
                    elif key == "min_age":
                        self.max_age = get_age(value)
                    else:
                        print("WARNING! Unprocessable key '{}' with value '{}'" . format(key, value))
                elif state == STATE__PRIOR_COMMANDS:
                    self.prior_commands.append(s)
                elif state == STATE__COMMANDS:
                    self.commands.append(s)
                elif state == STATE__POST_COMMANDS:
                    self.post_commands.append(s)
                    
    # ... end of class FFPConfig ...
                    

def get_last_word(s, allow_lower_letters = True, allow_upper_letters = True, allow_digits = True):
    LOWER_LETTERS = "abcdefghijklmnopqrstuvwxyz"
    UPPER_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    DIGITS = "0123456789"
    allowed = ""
    if allow_lower_letters:
        allowed += LOWER_LETTERS
    if allow_upper_letters:
        allowed += UPPER_LETTERS
    if allow_digits:
        allowed += DIGITS
    result = ""
    while len(s) > 0 and s[-1] in allowed:
        result = s[-1] + result
        s = s[0:len(s)-1]
    return result

#print(get_last_word("Hello 100World".lower(), True, False, False)); exit(0)
                    

def get_age(s):
    s = s.strip()
    if s == None:
        return None
    if len(s) == 0:
        return None
    multiplicator = 1
    if len(s) >= 2 and not s[-1].isdigit():
        # указаны единицы измерения (s=seconds, m=minutes, h=hours, d=days, w=weeks)
        measure = get_last_word(s.lower(), True, False, False)
        s = s[0:len(s)-len(measure)]
        s = s.strip()
        #print("[{}][{}]" . format(s, measure)); exit(0)
        if measure in ["s", "second", "seconds", "sec", "secs"]:
            multiplicator = 1
        elif measure in ["m", "minute", "minutes", "min", "mins"]:
            multiplicator = 60
        elif measure in ["h", "hour", "hours"]:
            multiplicator = 3600
        elif measure in ["d", "day", "days"]:
            multiplicator = 86400
        elif measure in ["w", "week", "weeks"]:
            multiplicator = 604800
        else:
            # недопустимая единица измерения
            return None
    try:
        cnt = int(s)
    except:
        return None
    cnt *= multiplicator
    return cnt

#print(get_age("12s")); exit(0)
#print(get_age(" 10m  ")); exit(0)
print(get_age(" 10 minutes  ")); exit(0)
#print(get_age("2H")); exit(0)
#print(get_age("10weeks")); exit(0)
#print(get_age("sd10weeks")); exit(0)


# ----- Текущие дата/время -----ы
def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ----- Из строки вида yyyy-mm-dd HH:MM:SS получить дату/время или None -----
def get_date_time_from_string(s):
    s = s.strip()   # убрать пробелы/табуляции в начале и конце
    #yyyy-mm-dd hh:mm:ss
    #0123456789012345678 {19}
    if len(s) < 10:
        # недостаточно символов чтобы быть датой
        return None
    year = None
    month = None
    day = None
    if (
        s[0].isdigit() and
        s[1].isdigit() and
        not(s[2].isdigit()) and
        s[3].isdigit() and
        s[4].isdigit() and
        not(s[5].isdigit()) and
        s[6].isdigit() and
        s[7].isdigit() and
        s[8].isdigit() and
        s[9].isdigit() and
        1 == 1
    ) :
        # dd.mm.yyyy hh:mm:ss
        # 0123456789012345678
        try:
            day = int(s[0:2])
            month = int(s[3:5])
            year = int(s[6:10])
        except:
            return None
    elif (
        s[0].isdigit() and
        s[1].isdigit() and
        s[2].isdigit() and
        s[3].isdigit() and
        not(s[4].isdigit()) and
        s[5].isdigit() and
        s[6].isdigit() and
        not(s[7].isdigit()) and
        s[8].isdigit() and
        s[9].isdigit() and
        1 == 1
    ) :
        # yyyy-mm-dd hh:mm:ss
        # 0123456789012345678
        try:
            year = int(s[0:4])
            month = int(s[5:7])
            day = int(s[8:10])
        except:
            return None
    else:
        return None
    hour = 0
    minute = 0
    second = 0
    micros = 0
    # dd.mm.yyyy hh:mm:ss
    # 0123456789012345678
    if len(s) >= 13:
        try:
            hour = int(s[11:13])
        except:
            return None
    if len(s) >= 16:
        try:
            minute = int(s[14:16])
        except:
            return None
    if len(s) >= 19:
        try:
            second = int(s[17:19])
        except:
            return None
        
    if len(s) >= 21 and not s[19].isdigit() :
        # микросекунды
        i = 20
        micros_str = ""
        while i < len(s) and i < 26:
            if s[i].isdigit():
                micros_str += s[i]
                i += 1

        n1 = len(micros_str)
        #print("micros_str:", micros_str, "  n1:", n1)
        # удалить ведущие нули
        leading_zeros_count = 0
        while len(micros_str) > 0 and micros_str[0] == "0":
            leading_zeros_count += 1
            micros_str = micros_str[1:len(micros_str)]
                
        try:
            micros = int(micros_str)
            #micros = float("0." + micros_str)
            n2 = 6 - n1
            for i in range(n2):
                micros *= 10
            #print("micros:", micros)
        except:
            return None

    try:
        result = datetime.datetime(year, month, day, hour, minute, second, micros)
    except:
        return None
    return result

#s = "\t 2025-06-27 09:26:05.0000123  "
#d = get_date_time_from_string(s)
#print(d)
#exit(0)

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


def get_files_list(dirname, files_masks, skip_newer, only_newer, min_age, max_age):
    found = []
    now = datetime.datetime.now()
    if os.path.isdir(dirname):
        items = os.listdir(dirname)
        #print("items:", items)
        for one_item in items:
            path = os.path.join(dirname, one_item)
            if os.path.isdir(path):
                continue
            if len(files_masks) > 0:
                # если указаны маски файлов, проверить на соответствие с масками файлов
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

            ctime = os.path.getctime(path)
            mtime = os.path.getmtime(path)
            atime = os.path.getatime(path)
            filetime = datetime.datetime.fromtimestamp(mtime)
            filetime_str = filetime.strftime("%Y-%m-%d %H:%M:%S")
            age = (now - filetime).total_seconds()
            if min_age != None or max_age != None:
                if min_age != None and age < min_age:
                    continue # файл слишком новый
                if max_age != None and age > max_age:
                    continue # файл слишком старый

            if only_newer != None or skip_newer != None:
                # указан диапазон дат файлов
                if only_newer != None:
                    if filetime < only_newer:
                        continue
                if skip_newer != None:
                    if filetime > skip_newer:
                        continue
            elem = {
                "shortname": one_item,
                "longname": path,
                "filesize": os.path.getsize(path),
                "ctime": ctime,
                "mtime": mtime,
                "atime": atime,
                "filetime": filetime_str,
                "age": age
            }

            found.append(elem)
    return found


# ----- Получить множество ранее обработанных файлов -----
# (в файле первый столбец дата/время обработки файла, потом через табуляцию - имя файла)
def read_processed_files(filename):
    result = set()
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
            ts, path = split_key_value(s, "\t")
            if ts == None or path == None or ts == "" or path == "":
                continue
            result.add(path)
    return result


def execute_commands(caption, commands, vars = {}):
    if caption != None and len(caption) > 0 and len(commands) > 0:
        # указано название команд и список команд не пустой
        print("--- {} ({}) ---" . format(caption, len(commands)))
    for i, one_cmd in enumerate(commands, 1):
        for key in vars.keys():
            if type(vars[key]) != type("abc"):
                # если атрибут не является строкой - сделать его строкой, чтобы можно было использовать в качестве значения переменной
                vars[key] = str(vars[key])
            one_cmd = one_cmd.replace("${" + key + "}", vars[key])
        print("  {}) {}" . format(i, one_cmd))
        os.system(one_cmd)
    if len(commands) > 0:
        print("")


# ----- Обработка конфигурационного файла -----
def process_config(config_path):
    if not os.path.isfile(config_path):
        print("File {} not found." . format(config_path))
        return False
    config = FFPConfig(config_path)
    #print("--- config: ---"); pprint(config.__dict__); print("--- end of config ---"); exit(0)
    files_list = []
    for elem in config.dir:
        files_list += get_files_list(elem, config.mask, config.skip_newer, config.only_newer, config.min_age, config.max_age)
    if config.sort_by != None:
        # newlist = sorted(list_to_be_sorted, key=lambda d: d['name'])
        #print("SortBy:", config.sort_by, "   reverse=", config.sort_reverse, sep=""); exit(0)
        files_list = sorted(files_list, key=lambda d: d[config.sort_by], reverse=config.sort_reverse)
    #print("--- files_list: ---"); pprint(files_list); print("... end of files_list ..."); exit(0)
    processed_files = read_processed_files(config.processed)

    execute_commands("prior-commands", config.prior_commands) # команды до обработки файлов

    f_processed = None
    if config.processed != None and len(config.processed) > 0:
        f_processed = open(config.processed, "at")
    for one_file_dict in files_list:
        if one_file_dict["longname"] in processed_files:
            # файл уже обрабатывался ранее
            print("skip file '{}' because it was processed earlier" . format(one_file_dict["longname"]))
            continue
        #print(one_file_dict)
        execute_commands('commands for "' + one_file_dict["longname"] + '"', config.commands, one_file_dict.copy())
        
        if f_processed != None:
            f_processed.write(
                get_timestamp() +
                "\t" +
                one_file_dict["longname"] + 
                "\n"
            )
    if f_processed != None:
        f_processed.close()

    execute_commands("post-commands", config.post_commands) # команды после обработки файлов

    return True


if __name__ == "__main__":
    process_config("config1.cfg"); exit(0)
    for i in range(1, len(sys.argv)):
        process_config(sys.argv[i])
    