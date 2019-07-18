#!/bin/bash

FLD=$1
#UTTY=$2

while : ; do
    sleep 1
    clear
    for d in $(find $FLD \( -type d -o -type l \) ); do
        echo "#-- $d"
        find $d/ -type f -maxdepth 1 | xargs ls -xstr | tail -5
    done
done #> $UTTY
