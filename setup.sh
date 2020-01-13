#!/bin/sh

if [ -f ./main.db ];
then
    # Drop old database sqlite
    rm main.db
    cat ./db/tables.sql | sqlite3 ./main.db
else
    # Create database sqlite
    cat ./db/tables.sql | sqlite3 ./main.db
fi

if [ -f ./xark.log ];
then
    # Drop old log file
    rm ./xark.log
fi
