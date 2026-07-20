#!/usr/bin/sh

# ###############################################
# Подсчёт суммарного размера файлов перечисленных в файле указанном в переменной filename
# или переданном как параметр командной строки.
# Суммарный размер подсчитывается в байтах, а также в гигабайтах если общий размер > 1 ГБ или
# в мегабайтах если общий размер < 1 ГБ.
#
# Пример команды, которой можно подготовить список файлов:
# find . -type f -name "*.txt" -size +500M -exec ls -l --time-style long-iso {} \; > seek_files_by_size_big.txt
#
# В файле с результатами поиска будут строки вида
# -r--------. 1 infodba dba 1059762176 2025-10-23 09:18 ./dir1/dir2/51d11de8/155_000_ugp_cpt03yobe6rjn.dat
# размер в байтах находится в пятом столбце
# ###############################################


export filename=seek_files_by_size_big.txt
if [ ! -z $1 ]
then
  filename=$1
fi

echo filename: $filename
if [ ! -f $filename ]
then
  echo ERROR!!! File \"$filename\" not found
  exit 1
fi

export lines_count=`cat $filename | wc -l`
echo lines_count: $lines_count

# --- цикл, выходя из которого переменная сохранит подсчитанную сумму
export summary_bytes=0
while read line ; do
  size=`echo $line | awk '{print $5}'`
  export summary_bytes=`expr $summary_bytes + $size`
done < $filename
echo summary_bytes: $summary_bytes bytes

export file_avg_size=`expr $summary_bytes / $lines_count`
echo file_avg_size: $file_avg_size bytes

export summary_megabytes=`expr $summary_bytes / 1048576`
if [ $summary_megabytes -lt 1025 ]
then
  echo summary_megabytes: $summary_megabytes megabytes
else
  export summary_gigabytes=`expr $summary_megabytes / 1024`
  echo summary_gigabytes: $summary_gigabytes gigabytes
fi
