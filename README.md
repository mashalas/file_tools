# Утилиты для работы с файлами и каталогами
## compare_dirs.py
Сравнить содержимое двух каталогов.
```
compare_dirs.py [параметры] <каталог1> <каталог2>
параметры:
  -s  --size   сравнивать размеры файлов
  -t  --time   сравнивать время модификации файлов
  -d  --data   сравнивать содержимое файлов
  --skip <item>  игнорировать файл или каталог.
      Если указан каталог не будет выполняться вход в этот каталог.
      Если указан файл не будет производиться сравнение этого файла с файлом из
      другого каталога с таким же именем.
```

---
