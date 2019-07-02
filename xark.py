#!/usr/bin/python

# -*- coding: utf-8 -*-
"""XO Agil Recolector Kaibil - XARK

Internal information collector of the XO. Currently collects:
    * Serial Number
    * UUID
    * Installed Activities
    * Journal Activity Metadata
    * RAM
    * ROM
    * Kernel
    * Procesor Architecture
    * MAC
"""

import os
import re
import sys
import time
import sched
import logging
import sqlite3
import datetime
import traceback
import subprocess
import multiprocessing

# Logging setting
logger = logging.getLogger("xark")
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)-s - %(message)s"
)
handler = logging.FileHandler(filename="xark.log", mode="a")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Conexion:
    """
    Connection class to sqlite3.

    Methods:
        get(query, data)
            Get a record from database.
        getmany(query, data)
            Get many records from database.
        set(query, data)
            Insert a record on database.
        setmany(query, data)
            Insert many records on database.
        close()
            Close connection to database.
    """

    def __init__(self):
        self.conn = sqlite3.connect("xark.db")
        self.c = self.conn.cursor()

    def get(self, query, data):
        """Get a record from a table.

        Args:
            query : str
                Query string.
            data : list
                List of tuples within query's parameters.

        Return:
            tuple
                Result record from table.
        """

        return self.c.execute(query, data).fetchone()

    def getmany(self, query, data):
        """Get many records from a table.

        Args:
            query : str
                Query string.
            data : list
                List of tuples within query's parameters.

        Return:
            list
                Result records from a table.
        """

        return self.c.execute(query, data).fetchall()

    def set(self, query, data):
        """Insert a record into a table.

        Args:
            query : str
                Query string.
            data : list
                List of tuples within query's parameters.

        Return:
            int
                Id of the last record inserted.
        """

        self.c.execute(query, data)
        self.conn.commit()

        return self.c.lastrowid

    def setmany(self, query, data):
        """Insert many record into a table.

        Args:
            query : str
                Query string.
            data : list
                List of tuples within query's parameters.

        Return:
            int
                Id of the last record inserted.
        """

        self.c.executemany(query, data)
        self.conn.commit()

        return self.c.lastrowid

    def close(self):
        """Close connection to database."""

        self.c.close()
        self.conn.close()


class Xark:
    """
    Xark class for extract device info from xo laptop.

    Methods:
        addFirst(data, item)
        collection()
        extracData()
        extracJournal()
        extracLogs()
        getActivityHistory()
        getArch()
        getDailyId()
        getInfoJournal(dir)
        getMac()
        getRam()
        getRom()
        getSerial()
        getKernel()
        readFile(self, file_dir, file_name)
        synchrome()
    """

    def __init__(self):
        self.db = Conexion()
        # Fecha actual en entero
        self.day = int(datetime.datetime.now().strftime("%Y%m%d"))
        # Obtenr el identificador de la laptop
        id = self.getSerial()
        self.serialnum = id["serialnum"]
        self.uuid = id["uuid"]
        # Verificar estado diario del kaibil
        self.dayid = None
        response = self.db.get(
            "SELECT * FROM xk_status WHERE date_print = ?", [(self.day)]
        )
        if response is None:
            self.dayid = self.db.set(
                "INSERT INTO xk_status(serial_num, uuid, date_print) VALUES(?, ?, ?)",
                [(self.serialnum), (self.uuid), (self.day)],
            )
        else:
            self.dayid = self.getDailyId()

        # Directorio de metadata del Diario
        self.work_dir = "~/.sugar/default/datastore/"
        # Programador de frecuencia de peticiones
        self.s = sched.scheduler(time.time, time.sleep)

    def getDailyId(self):
        response = self.db.get(
            "SELECT id_status FROM xk_status WHERE date_print = ?",
            [(self.day)],
        )

        return int(response[0])

    def getSerial(self):
        """Capturar Numero de serie y UUID"""
        data = dict()
        f = open("/home/.devkey.html", "r")
        for value in f:
            if "serialnum" in value or "uuid" in value:
                value = value.strip().split(" ")
                data[value[2].split("=")[1].replace('"', "")] = (
                    value[3].split("=")[1].replace('"', "")
                )

        return data

    def addFirst(self, data, item):
        """Agrega un elemento a un tupla a inicio de la tupla.
        Args:
            data (tuplr): Tupla a la que se agregara el elemento.
            item (str): Elemento que se agregara a la tupla.
        Returns:
            tuple: Tupla con el item agregado al inicio.
        """
        tmp_list = list(data)
        tmp_list.insert(0, item)

        return tuple(tmp_list)

    def readFile(self, file_dir, file_name):
        """Lee el contenido de archivo de metadata.
        Args:
            file_dir (str): Ruta al directorio de metadata.
            file_name (str): Nombre del archivo a leer.
        Returns:
            dict: Nombre del archivo: Contenido del archivo.
        """
        contents = ""
        if os.path.isfile("{}/metadata/{}".format(file_dir, file_name)):
            f = open("{}/metadata/{}".format(file_dir, file_name), "r")
            contents = f.read()
            if contents is None or contents == "":
                contents = "Empty"
        else:
            contents = "Empty"

        return contents

    def getInfoJournal(self, dir):
        """Lee y lista cada archivo en el directorio de metadata.
        Args:
            dir (str): Ruta al directorio de metadata.
        Returns:
            list: Lista de contenidos del diccionario.
        """
        data_name = [
            "activity",
            "activity_id",
            "checksum",
            "creation_time",
            "filesize",
            "icon-color",
            "keep",
            "launch-times",
            "mime_type",
            "mountpoint",
            "mtime",
            "share-scope",
            "spent-times",
            "timestamp",
            "title",
            "title_set_by_user",
            "uid",
        ]

        if dir not in [
            "index",
            "checksums",
            "index_updated",
            "version",
            "ds_clean",
        ]:
            in_dir = subprocess.Popen(
                "ls -d {}{}/*".format(self.work_dir, dir),
                shell=True,
                stdout=subprocess.PIPE,
            ).stdout.readlines()
            info = tuple(
                map(lambda x: self.readFile(in_dir[0].strip(), x), data_name)
            )
            info = self.addFirst(info, self.dayid)

            return info

    def extracJournal(self):
        """Lee y extrae la informacion de metadata del diaro.
        Returns:
            list: Lista de contenidos de cada archivo de metadata.
        """
        salida = subprocess.Popen(
            "ls {}".format(self.work_dir), shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        salida = list(x.strip() for x in salida)
        info = map(lambda x: self.getInfoJournal(x), salida)
        info = filter(lambda x: x, info)

        return info

    def getActivityHistory(self):
        lista = ""
        salida = subprocess.Popen(
            "ls ~/Actividades/", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        for i, v in enumerate(salida):
            if i < len(salida) - 1:
                lista += v.strip() + ","
            else:
                lista += v.strip()

        return lista

    def getRam(self):
        ram = ""
        salida = subprocess.Popen(
            "free -m", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        mem = re.sub(r"\s+", " ", salida[1])
        swap = re.sub(r"\s+", " ", salida[2])

        for i, v in enumerate(mem.strip().split(" ")):
            if i > 0 and i <= 3:
                if i < 3:
                    ram = ram + v + ","
                else:
                    ram = ram + v

        ram = ram + "|"

        for i, v in enumerate(swap.strip().split(" ")):
            if i > 0 and i <= 3:
                if i < 3:
                    ram = ram + v + ","
                else:
                    ram = ram + v

        return ram

    def getRom(self):
        rom = ""
        salida = subprocess.Popen(
            "df -H --output=source,size,used,avail,target",
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()
        for i in salida:
            dir = re.sub(r"\s+", " ", i.strip())
            if "/dev/" in dir.split(" ")[0]:
                for x, y in enumerate(dir.split(" ")):
                    if x > 0 and x <= 4:
                        if x < 4:
                            rom = rom + y + ","
                        else:
                            rom = rom + y
                rom = rom + "|"
        rom = rom[:-1]

        return rom

    def getKernel(self):
        kernel = subprocess.Popen(
            "uname -a", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        kernel = kernel[0].strip().split("#")[0].strip()
        return kernel

    def getArch(self):
        arch = ""
        salida = subprocess.Popen(
            "lscpu", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        arch = arch + re.sub(r"\s+", " ", salida[0].strip()).split(" ")[1]
        arch = arch + "|"
        arch = arch + re.sub(r"\s+", " ", salida[4].strip()).split(" ")[1]
        arch = arch + "|"
        arch = (
            arch
            + re.sub(r"\s+", " ", salida[13].strip()).split(":")[1].strip()
        )

        return arch

    def getMac(self):
        iface = "wlp2s0"
        mac = subprocess.Popen(
            "cat /sys/class/net/{}/address".format(iface),
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()

        return mac[0].strip()

    def extracData(self):
        data = list()
        data.append(self.getActivityHistory())
        data.append(self.getRam())
        data.append(self.getRom())
        data.append(self.getKernel())
        data.append(self.getArch())
        data.append(self.getMac())
        data.insert(0, self.dayid)

        return tuple(data)

    def extracLogs(self):
        print(True)

        return True

    def collection(self):
        """Recolectar informacion de la laptop xo.
        Returns:
            bool: True/False.
        """
        response = self.db.get(
            "SELECT collect_status FROM xk_status WHERE date_print = ?",
            [(self.day)],
        )
        if bool(int(response[0])):
            # La informacion para el dia ya se ha rocolectado.
            # Termina la funcion.
            return bool(int(response[0]))

        # Extraer informacion del diario y guadarlo en la base de datos.
        journal = self.extracJournal()
        self.db.setmany(
            "INSERT INTO xk_journal_xo(xark_status_id, activity, activity_id, checksum, creation_time, file_size, icon_color, keep, launch_times, mime_type, mountpoint, mtime, share_scope, spent_times, time_stamp, title, title_set_by_user, uid) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            journal,
        )

        # Extraer informacion del dispocitivo
        data = self.extracData()
        self.db.set(
            "INSERT INTO xk_data_xo(xark_status_id, activities_history, ram, rom, kernel, arqc, mac) VALUES(?, ?, ?, ?, ?, ?, ?)",
            data,
        )

        response_j = self.db.get(
            "SELECT COUNT(*) FROM xk_journal_xo WHERE xark_status_id = ?",
            [(self.dayid)],
        )
        response_d = self.db.get(
            "SELECT COUNT(*) FROM xk_data_xo WHERE xark_status_id = ?",
            [(self.dayid)],
        )
        if int(response_j[0]) >= 1 and int(response_d[0]) >= 1:
            # Estado de sincronizacion en `Sincronizado`
            self.db.set(
                "UPDATE xk_status set collect_status = ?, collect_date = ? WHERE date_print = ?",
                [(True), (datetime.datetime.now()), (self.day)],
            )

            return True
        else:
            return False

    def synchrome(self):
        """Sincronizar con el charco."""
        server = "http://192.168.8.109:5000/"
        user = "olpc"

        response = self.db.get(
            "SELECT sync_status, collect_status FROM xk_status WHERE date_print = ?",
            [(self.day)],
        )
        if bool(int(response[0])) and bool(int(response[1])):
            # Termina la funcion si ya se a sincronizacion con el charco
            return bool(int(response[0]))

        # Verifica si el IIAB esta disponible
        request_url = (
            'curl -o /dev/null -w "%{http_code}\\n" -X POST '
            + server
            + ' -d "user='
            + user
            + "&client_id="
            + self.serialnum
            + "&client_secret="
            + self.uuid
            + '"'
        )
        code = subprocess.Popen(
            request_url, shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        code = int(code[0].strip())
        if code == 200 and bool(int(response[1])):
            data = dict()

            journal = self.db.getmany(
                "SELECT activity, activity_id, checksum, creation_time, file_size, icon_color, keep, launch_times, mime_type, mountpoint, mtime, share_scope, spent_times, time_stamp, title, title_set_by_user, uid FROM xk_journal_xo WHERE xark_status_id = ?",
                [(self.dayid)],
            )
            if journal is not None:
                data["journal"] = list(
                    list(i.encode() for i in x) for x in journal
                )
            else:
                data["journal"] = list(list(map("Empty", range(17))))

            device = self.db.getmany(
                "SELECT activities_history, ram, rom, kernel, arqc, mac FROM xk_data_xo WHERE xark_status_id = ?",
                [(self.dayid)],
            )
            if device is not None:
                data["device"] = list(
                    list(i.encode() for i in x) for x in device
                )
            else:
                data["device"] = list(list(map("Empty", range(6))))

            request_url = (
                "curl -u "
                + self.serialnum
                + ":"
                + self.uuid
                + ' -o /dev/null -w "%{http_code}\\n" -X POST '
                + server
                + "data -d "
                + '"grant_type=password&username='
                + user
                + '&password=valid&scope=profile&data={}"'.format(data)
            )
            result = subprocess.Popen(
                request_url, shell=True, stdout=subprocess.PIPE
            ).stdout.readlines()
            result = int(result[0].strip())
            if result == 200:
                self.db.set(
                    "UPDATE xk_status set sync_status = ?, sync_date = ? WHERE date_print = ?",
                    [(True), (datetime.datetime.now()), (self.day)],
                )
                return True
        else:
            self.s.enter(10, 1, self.synchrome, ())
            self.s.run()


def cath_Exception(tb_except):
    """Captura traceback y excepciones para guardaelas en xark_except.
    Args:
        tb_except (str): Excepcion.
    """
    # Tipo de la excepcion.
    except_type = str(sys.exc_info()[0])
    except_type = except_type.split("'")[1]
    # Mensaje de la excepcion.
    except_message = sys.exc_info()[1]
    # Captura traceback.
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[len(traceback.format_tb(tb)) - 1]
    # Nombre del script.
    file_name = tbinfo.split(",")[0].strip()
    # Linea de la excepcion.
    file_line = tbinfo.split(",")[1].strip()
    # Fragmento de codigo de la excepcion.
    except_code = tbinfo.split(",")[2].strip()

    Conexion().set(
        "INSERT INTO xk_excepts(except_type, except_messg, file_name, file_line, except_code, tb_except, user_name) VALUES(?, ?, ?, ?, ?, ?, ?)",
        [
            (except_type.replace("'", '"')),
            (str(except_message).replace("'", '"')),
            (file_name.replace("'", '"')),
            (file_line.replace("'", '"')),
            (except_code.replace("'", '"')),
            (str(tb_except).replace("'", '"')),
            (os.environ["USER"].replace("'", '"')),
        ],
    )

    return True


if __name__ == "__main__":
    """Flujo prinvipal de ejecucion."""

    # Log de inicio diario
    logger.info(
        "Inicio de la ejecucion del dia {}".format(datetime.datetime.now())
    )

    try:
        # Instancia del Kaibil
        xark = Xark()

        # Verifica si el dia de la semana es entre lunes y viernes
        if (
            datetime.datetime.now().weekday() >= 0
            and datetime.datetime.now().weekday() <= 4
        ):
            # Verifica que la hora del dia sea entre las 6:00 y las 18:00
            if datetime.datetime.now().time() >= datetime.time(
                6, 0
            ) and datetime.datetime.now().time() <= datetime.time(18, 0):
                # Recolectar informacion
                multiprocessing.Process(
                    target=xark.collection, args=()
                ).start()
                # Sincronizar con el charco
                multiprocessing.Process(target=xark.synchrome, args=()).start()

                # close connection
                Conexion().close()
            else:
                logger.info(
                    "Hora del dia {} fuera del rango 6:00 a 18:00".format(
                        datetime.datetime.now().time()
                    )
                )

        else:
            logger.info(
                "Dia de la semana {} no de lunes a viernes".format(
                    datetime.datetime.now().weekday()
                )
            )

    except Exception() as e:
        logger.error("Exception: {}".format(e))
        print(e)
        cath_Exception(e)
        sys.exit(1)

#    ___    ___ ________  ________  ___  __
#   |\  \  /  /|\   __  \|\   __  \|\  \|\  \
#   \ \  \/  / | \  \|\  \ \  \|\  \ \  \/  /|_
#    \ \    / / \ \   __  \ \   _  _\ \   ___  \
#     /     \/   \ \  \ \  \ \  \\  \\ \  \\ \  \
#    /  /\   \    \ \__\ \__\ \__\\ _\\ \__\\ \__\
#   /__/ /\ __\    \|__|\|__|\|__|\|__|\|__| \|__|
#   |__|/ \|__| Baby SAHRK hunting for device information without supervision.
