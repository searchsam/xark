#!/bin/#!/bin/sh

# Crea la base datos para sqlite3 limpia
if [ -f ./xark.db ];
then
    # Drop old database sqlite
    rm xark.db
    cat ./db/tables.sql | sqlite3 ./xark.db
else
    # Create database sqlite
    cat ./db/tables.sql | sqlite3 ./xark.db
fi

# Eliminar el archivo log
if [ -f ./xark.log ];
then
    # Drop old log file
    rm ./xark.log
fi

# Crea la unidad de servicios
if [ -f ./xarkd.service ];
then
    # Drop old log file
    rm ./xarkd.service
    echo "[Unit]
Description=Put kaibil to work
After=network.target

[Service]
Type=simple
WorkingDirectory=.
ExecStart=/usr/bin/python ./xark.py
KillMode=process

[Install]
WantedBy=multi-user.target" > xarkd.service
else
    echo "[Unit]
Description=Put kaibil to work
After=network.target

[Service]
Type=simple
WorkingDirectory=.
ExecStart=/usr/bin/python ./xark.py
KillMode=process

[Install]
WantedBy=multi-user.target" > xarkd.service
fi
