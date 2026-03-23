
import sys

SEP = '\t'                  # символ-разделитель
MULTISEPS_AS_ONE = True     # несколько идущих подряд разделителей восприимать как один
SKIP_HEADER = True          # игнорировать первую строку файла (заголовок)
SORT_BY__KEY = "k"          # сортировать по ключу
SORT_BY__VALUE = "v"        # сортировать по значению
SORT_BY = SORT_BY__KEY    # столбец сортировки
SORT_DESCENDING = True      # сортировка в обратном порядке


def kv_sum_from_file(filename, kv):
    with open(filename, 'rt') as f:
        n = 0
        for s in f:
            s = s.strip()
            if len(s) == 0:
                continue

            n += 1
            if n == 1 and SKIP_HEADER:
                continue # первая непустая строка и нужно пропустить строку с заголовком

            if MULTISEPS_AS_ONE:
                while s.find(SEP + SEP) >= 0:
                    s = s.replace(SEP + SEP, SEP)

            parts = s.split(SEP)
            if len(parts) != 2:
                continue
            key = parts[0]
            try:
                value = int(parts[1])
            except:
                # не удалось конвертировать строку в число - пропустить эту строку
                print('WARNING! Cannot convert [{}] to integer on line number #{} from file [{}]' . format(parts[1], n, filename), file=sys.stderr)
                print('  Whole line: [{}]' . format(s), file=sys.stderr)
                continue
            if key in kv:
                kv[key] += value
            else:
                kv[key] = value
            

if __name__ == '__main__':
    kv = {}
    for i in range(1, len(sys.argv)):
        # проход по всем переданным в командной строке файлам
        kv_sum_from_file(sys.argv[i], kv)

    keys = list(kv.keys())
    if SORT_BY == SORT_BY__KEY:
        keys.sort(reverse=SORT_DESCENDING)
    elif SORT_BY == SORT_BY__VALUE:
        kva = []
        for key in keys:
            kva.append([key, kv[key]])
        kva.sort(key=lambda row: row[1], reverse=SORT_DESCENDING)
        keys = [row[0] for row in kva]
    for key in keys:
        print(key + '\t' + str(kv[key]))
