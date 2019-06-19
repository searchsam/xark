#!/bin/#!/bin/sh

# Create database sqlite
cat db/tables.sql | sqlite3 main.db
