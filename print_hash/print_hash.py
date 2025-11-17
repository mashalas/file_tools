
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


def get_hash__crc32(filename):
    result = ''
    if not os.path.isfile(filename):
        return result
    try:
        with open(filename, 'rb') as f:
            buf = f.read()
            result = hex(zlib.crc32(buf))
        
        #   1234567	=>	  12345678
        # 0x3a68d61	=>	0x03a68d61
        while len(result) < 10:
            # добавить ведущие нули
            result = result[0:2] + '0' + result[2:len(result)]
    except:
        result = '0x????????'
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


def get_hash(filename, algo):
    result = ""
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
        result = 'unknown algorithm of hash-sum calculating: "{}"' . format(algo)
    return result


def print_hash(path, algo):
    prefix = ''
    if path.find('*') >= 0 or path.find('?') >= 0:
        # указана маска файлов
        items = glob.glob(path)
        for one_item in items:
            next_path = os.path.join(os.path.curdir, one_item)
            print_hash(next_path, algo)
    elif os.path.isdir(path):
        # указан каталог
        items = os.listdir(path)
        for one_item in items:
            next_path = os.path.join(path, one_item)
            print_hash(next_path, algo)
    elif os.path.isfile(path):
        # указан файл
        hash_value = get_hash(path, algo)
        print('{}{}  {}' . format(prefix, hash_value, path))
    

def help():
    print('print_hash.py <file|dir|mask>')
    print('Calculate hash-sum for file, directory with subdirectories or files matched with mask')
    print('By default calculates crc32. Another algorithm cat be specified in environment variable "HASH_ALGO".')
    algorithms = ['crc32']
    algorithms += HASHLIB_ALOGORITHMS
    algorithms_str = ', '.join(algorithms)
    print('Available algorithms:', algorithms_str)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('No files specified.\n')
        help()
        exit(1)
    if sys.argv[1] in ('-h', '--help', '-help', '/?', '-?'):
        help()
        exit(0)
    algo = os.environ.get('HASH_ALGO')
    if algo == None:
        algo = DEFAULT_HASH_ALGORITHM
    for i in range(1, len(sys.argv)):
        print_hash(sys.argv[i], algo)
