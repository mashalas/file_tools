#!/usr/bin/python3

import os
import fnmatch


ROOT_DIR = 'dir1'               # каталог, в котором выполнять замену
VARS = {                        # словарь, в котором ключ - имя искомого шаблона, значение - на что заменить
    'tpl1': 'value1',
    'tpl2': 'value2'
}
REPLACE_IN_DIR_NAMES = True     # выполнять замену в именах файлов
REPLACE_IN_FILE_NAMES = True    # выполнять замену в именах каталогов
REPLACE_IN_CONTENTS = True      # выполнять замену в содержимом файлов
TEMPLATE_OPEN_SEQUENCE = '{{'   # открывающая последовательность шаблона, например {{ или ${
TEMPLATE_CLOSE_SEQUENCE = '}}'  # закрывающая последовательность шаблона, напрмиер }} или }
FILES_MASKS = (                 # список масок файлов (вида *.txt, *.ini) для которых выполнять замену в тексте этих файлов
    '*.txt',                    # если пустой список масок файлов - выполнять замену во всех файлах
    '*.ini'
)

def substitute(src, vars, template_open_sequence, template_close_sequence):
    dst = src
    for key in vars.keys():
        seek = template_open_sequence + key + template_close_sequence
        replace_to = vars[key]
        #print(key, seek)
        dst = dst.replace(seek, replace_to)
    return dst


# ----- Выполнить замену в имени файла или каталога -----
def rename_fs_item(dirname, fs_item, vars, template_open_sequence, template_close_sequence):
    old_name = fs_item
    new_name = substitute(old_name, vars, template_open_sequence, template_close_sequence)
    if new_name != old_name:
        # переименовать файл/каталог
        old_path = os.path.join(dirname, old_name)
        new_path = os.path.join(dirname, new_name)
        os.rename(old_path, new_path)
        path = os.path.join(dirname, new_name)
    else:
        # имя файла/каталога не меняется
        path = os.path.join(dirname, new_name)
    return path # возвращается новое имя файла/каталога уже после переименования


# ----- Выполнить замену в тексте файла -----
def do_replace_in_contents(dirname, filename_short, vars, template_open_sequence, template_close_sequence, files_masks):
    replaced_lines_count = -1
    if len(files_masks) > 0:
        # если указаны маски файлов, проверить на соответствие с масками файлов
        # если маски не указаны - выполнять замену во всех файлах
        matched = False
        for one_mask in files_masks:
            ok = fnmatch.fnmatch(filename_short, one_mask)
            if ok:
                matched = True
                break # если совпадение имени файла с одной из масок, то остальные маски можно не проверять
        if not matched:
            # имя текущего файла не совпало ни с одной допустимой маской файлов
            #print("skip:", one_item)
            return replaced_lines_count # файл не читался
    replaced_lines_count = 0
    path = os.path.join(dirname, filename_short)
    lines = []
    f = open(path, 'rt')
    for s1 in f:
        s1 = s1.strip()
        s2 = substitute(s1, vars, template_open_sequence, template_close_sequence)
        lines.append(s2)
        if s1 != s2:
            replaced_lines_count += 1
    f.close()
    #print('lines:', lines, replaced_lines_count)
    #return 0
    if replaced_lines_count > 0 and len(lines) > 0:
        # некоторые строки были изменены - перезаписать файл с новым содержимым
        f = open(path, 'wt')
        for s in lines:
            f.write(s + '\n')
        f.close()
    return replaced_lines_count # файл был прочитан, вернуть сколько строк были изменены


# ----- Рекурсивный обход каталогов для переименования подкаталогов, файлов и замены в тексте файлов
def dirwalk(
        root_dir,                       # каталог, в котором выполнять замену
        vars,                           # словарь, в котором ключ - имя искомого шаблона, значение - на что заменить
        replace_in_dir_names,           # выполнять замену в именах файлов
        replace_in_file_names,          # выполнять замену в именах каталогов
        replace_in_contents,            # выполнять замену в содержимом файлов
        template_open_sequence,         # открывающая последовательность шаблона, например {{ или ${
        template_close_sequence,        # закрывающая последовательность шаблона, напрмиер } или }
        files_masks                     # список масок файлов (вида *.txt, *.ini) для которых выполнять замену в тексте этих файлов; пустой список - выполнять замену во всех файлах
):
    #print('enter to:', root_dir)
    items = os.listdir(root_dir)
    #print(items)
    for one_item in items:
        path = os.path.join(root_dir, one_item)
        #print(path)
        if os.path.isdir(path):
            # dir
            if replace_in_dir_names:
                path = rename_fs_item(root_dir, one_item, vars, template_open_sequence, template_close_sequence)
            dirwalk(path, vars, replace_in_dir_names, replace_in_file_names, replace_in_contents, template_open_sequence, template_close_sequence, files_masks)
        else:
            # file
            content_was_checked = False
            if replace_in_contents:
                do_replace_in_contents(root_dir, one_item, vars, template_open_sequence, template_close_sequence, files_masks)
                content_was_checked = True
            if replace_in_file_names:
                path = rename_fs_item(root_dir, one_item, vars, template_open_sequence, template_close_sequence)
            if replace_in_contents and not content_was_checked:
                do_replace_in_contents(root_dir, one_item, vars, template_open_sequence, template_close_sequence, files_masks)
            pass


if __name__ == '__main__':
    dirwalk(
        ROOT_DIR,
        VARS,
        REPLACE_IN_DIR_NAMES,
        REPLACE_IN_FILE_NAMES,
        REPLACE_IN_CONTENTS,
        TEMPLATE_OPEN_SEQUENCE,
        TEMPLATE_CLOSE_SEQUENCE,
        FILES_MASKS
    )
    