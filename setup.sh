#!/bin/#!/bin/sh

# Drop old database sqlite
rm main.db
# Create database sqlite
cat db/tables.sql | sqlite3 main.db
# Drop old log file
rm xark.log
