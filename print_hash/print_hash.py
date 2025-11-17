
import os
import sys
import hashlib
import zlib
import glob

DEFAULT_HASH_ALGORITHM = 'crc32'
HASHLIB_ALOGORITHMS = hashlib.algorithms_available
HASHLIB_ALOGORITHMS.remove('shake_128')
HASHLIB_ALOGORITHMS.remove('shake_256')
HASHLIB_ALOGORITHMS = list(HASHLIB_ALOGORITHMS) # чтобы можно было сортировать
HASHLIB_ALOGORITHMS.sort()

ALL_AVAILABLE_ALGORITHMS = ['crc32']
ALL_AVAILABLE_ALGORITHMS += HASHLIB_ALOGORITHMS

HASH_SPLIT_SYMBOL = '-'


# ----- Разделить строку на блоки по split_size символов используя в качестве разделителя split_symbol -----
# (возможно разделение не с первого символа, а с позиции split_since)
def str_split_to_groups(s, split_size, split_symbol = HASH_SPLIT_SYMBOL, split_since = 0):
    if split_size <= 0:
        return s
    result = ''
    # 01234567    01 234 567 8
    # abcdefghi   ab cde fgh i
    since = split_since
    if since > 0:
        result = s[0:since] + split_symbol
    #for i in range(split_since, len(s), split_size):
    while since < len(s):
        until = since + split_size
        result += s[since:until]
        if until < len(s):
            result += split_symbol
        since = until
    return result


def get_hash__crc32(filename):
    result = ''
    if not os.path.isfile(filename):
        return result
    try:
        with open(filename, 'rb') as f:
            buf = f.read()
            result = hex(zlib.crc32(buf))
        if len(result) > 2 and result[0:2] == '0x':
            result = result[2:len(result)] # убрать признак 16-ричности (0x)
        result = result.upper()
        while len(result) < 8:
            # добавить ведущие нули
            result = '0' + result
    except:
        result = '????????'
    return result

def get_hash__from_hashlib(filename, algo, block_size = 2**20):
    result = ''
    if not os.path.isfile(filename):
        return result
    try:
        with open(filename, 'rb') as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                algo.update(data)
            result = algo.hexdigest()
    except:
        result = ''
    return result


def get_hash(filename, algo, split_count = 0, split_symbol = HASH_SPLIT_SYMBOL):
    result = ""
    ok = True
    if not os.path.isfile(filename):
        return result
    if algo.lower() == 'crc32':
        # +++ crc32 with zlib +++
        result = get_hash__crc32(filename)
    elif algo in HASHLIB_ALOGORITHMS:
        # +++ алгоритмы из hashlib +++
        BLOCK_SIZE = 2**20
        algo_hashlib = hashlib.new(algo)
        result = get_hash__from_hashlib(filename, algo_hashlib, BLOCK_SIZE)
    else:
        ok = False
        result = 'unknown algorithm of hash-sum calculating: "{}"' . format(algo)
    if ok:
        if split_count > 0 and split_symbol != '':
            result = str_split_to_groups(result, split_count, split_symbol)
    return result


def print_hash(path, algo_list, hash_split):
    if path.find('*') >= 0 or path.find('?') >= 0:
        # указана маска файлов
        items = glob.glob(path)
        for one_item in items:
            next_path = os.path.join(os.path.curdir, one_item)
            print_hash(next_path, algo_list, hash_split)
    elif os.path.isdir(path):
        # указан каталог
        items = os.listdir(path)
        for one_item in items:
            next_path = os.path.join(path, one_item)
            print_hash(next_path, algo_list, hash_split)
    elif os.path.isfile(path):
        # указан файл
        msg = path
        for a in algo_list:
            msg += '\t' + get_hash(path, a, hash_split)
            #one_hash = get_hash(path, a)
            #if a == 'crc32' and len(one_hash) > 2:
            #    one_hash = 
            #msg += '\t' + one_hash
        print(msg)
    

def help():
    print('print_hash.py <file|dir|mask>')
    print('Calculate hash-sum for file, directory with subdirectories or files matched with mask')
    print('By default calculates crc32. Another algorithm cat be specified in environment variable "HASH_ALGO".')
    algorithms_str = ', '.join(ALL_AVAILABLE_ALGORITHMS)
    print('Available algorithms:', algorithms_str)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('No files specified.\n')
        help()
        exit(1)
    if sys.argv[1] in ('-h', '--help', '-help', '/?', '-?'):
        help()
        exit(0)
    algo_str = os.environ.get('HASH_ALGO')
    if algo_str == None:
        algo_str = DEFAULT_HASH_ALGORITHM
    algo_str = algo_str.replace(',', ' ')
    algo_list = algo_str.split(' ')
    algo_list = list(filter(None, algo_list)) # удалить пустые элементы
    algo_list = [a for a in algo_list if a in ALL_AVAILABLE_ALGORITHMS] # оставить только допустимые значения
    #print(algo_list); exit(0)

    # делить ли контрольную сумму на блоки по <hash_split> символов
    hash_split = 0
    if not os.environ.get('HASH_SPLIT') is None:
        try:
            hash_split_str = os.environ.get('HASH_SPLIT')
            hash_split = int(hash_split_str)
        except:
            hash_split = 0
    
    # --- заголовок: имя файла и названия алгоритмов
    msg = 'filename'
    for a in algo_list:
        msg += '\t' + a
    print(msg)

    for i in range(1, len(sys.argv)):
        print_hash(sys.argv[i], algo_list, hash_split)
