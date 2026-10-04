#!/usr/bin/env sh

export name=$1
if [ "$name" == "" ]
then
  echo Directory of file are not specified
  exit
fi

export DATE=$(date '+%Y-%m-%d')
export backup_prefix=${name}__${DATE}
export letters=abcdefghijklmnopqrstuvwxyz
export letters_count=${#letters}

export format=zip
#export format=tgz
#export format=7z

export counter=-2
unset backup_cmd
while true
do
  counter=`expr $counter + 1`
  unset date_uniquizer
  if [ $counter -ge 0 ]
  then
    if [ $counter -lt $letters_count ]
    then
      export date_uniquizer="${letters:$counter:1}"
    else
      #export backup_prefix=${backup_prefix}_
      export date_uniquizer=`expr $counter - $letters_count`
      export date_uniquizer=`expr $date_uniquizer + 1`
      export date_uniquizer=~${date_uniquizer}
    fi
  fi
  export backup_candidate=${backup_prefix}${date_uniquizer}.${format}
  if [ ! -f $backup_candidate ]
  then
    # принимается имя кандидата, т.к. архива с таким именем ещё нет
    unset backup_cmd
    export archive_name=$backup_candidate
    if [ "$format" = "zip" ]
    then
      if [ -d $name ]
      then
        # архивирусется каталог
        export backup_cmd="zip -r9 $archive_name $name"
      else
        # архивируется файл
        export backup_cmd="zip -9 $archive_name $name"
      fi
    fi
    if [ "$format" = "tgz" ]
    then
      export backup_cmd="tar -cvf - $name | gzip -9c > $archive_name"
    fi
    if [ "$format" = "7z" ]
    then
      export backup_cmd="7z a -mx9 $archive_name $name"
    fi
    break
  fi
done

if [ -v backup_cmd ]
then
  eval $backup_cmd
  echo ---------------------------------------
  echo ---\[ $backup_cmd \]---
  echo ---------------------------------------
else
  echo backup_cmd is not defined
fi
