#!/bin/#!/bin/sh

if [ -f ./xark.db ];
then
    # Drop old database sqlite
    rm xark.db
    cat ./db/tables.sql | sqlite3 ./xark.db
else
    # Create database sqlite
    cat ./db/tables.sql | sqlite3 ./xark.db
fi

if [ -f ./xark.log ];
then
    # Drop old log file
    rm ./xark.log
fi
