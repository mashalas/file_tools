#!/usr/bin/sh

# начальный каталог, с которого производить поиск
root_dir=.

# строка для поиска
search_string=Gpl

# 1 - игнорировать регистр, остальное - учитывать регистрп
ignore_case=1

# для размеров признак байтов - символ c, если не указан символ - размер в 512-байтных блоках
min_size_bytes=10000
max_size_bytes=50000

min_age_days=-1
max_age_days=10
#искать файлы, созданные позже, чем другой_файл
newer=-no-file

cmd="find $root_dir -type f"

# минмальный размер в байтах
if [ $min_size_bytes -gt 0 ]
then
  cmd="$cmd -size +${min_size_bytes}c"
fi

# максимальный размер в байтах
if [ $max_size_bytes -gt 0 ]
then
  cmd="$cmd -size -${max_size_bytes}c"
fi

# файлы изменённые ранее N дней назад
if [ $min_age_days -gt 0 ]
then
  cmd="$cmd -mtime +${min_age_days}"
fi

# файлы изменённые за последние N дней
if [ $max_age_days -gt 0 ]
then
  cmd="$cmd -mtime -${max_age_days}"
fi

# файлы новее указанного
if [ -f $newer ]
then
  cmd="$cmd -newer $newer"
fi

# -n - выводить номера строк с найденной последовательностью
cmd="$cmd -exec grep --line-number"

# игнорировать ли регистр
if [ "$ignore_case" == "1" ]
then
  cmd="$cmd --ignore-case"
fi

#cmd="$cmd -exec ls -l {} \;"
cmd="$cmd \"$search_string\" {} +"
echo $cmd
#$cmd \;
#exec $cmd
#sh -c $cmd
