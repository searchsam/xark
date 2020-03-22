#!/usr/bin/env bash

# Leer el archivo .env con las variables de entorno.
if [ -f ./.env ]
then
    declare -A ENV
    while IFS='=' read -r key value; do
        ENV[$key]=$value
    done < ./.env
fi

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
WorkingDirectory=${ENV[WORKING_DIRECTORY]}
ExecStart=/usr/bin/python ${ENV[WORKING_DIRECTORY]}.xark/xark.py
KillMode=process

[Install]
WantedBy=multi-user.target" > xarkd.service
else
    echo "[Unit]
Description=Put kaibil to work
After=network.target

[Service]
Type=simple
WorkingDirectory=${ENV[WORKING_DIRECTORY]}
ExecStart=/usr/bin/python ${ENV[WORKING_DIRECTORY]}.xark/xark.py
KillMode=process

[Install]
WantedBy=multi-user.target" > xarkd.service
fi
sudo mv xarkd.service /etc/systemd/system/.
