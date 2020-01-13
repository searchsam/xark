#!/usr/bin/python

"""
XO Agil Recolector Kaibil - XARK

Recolector de informacion interno de la XO. Actualmentle solo recolecta:
    * Numero de serie (Serial Number)
    * UUID (Universally Unique IDentifier)
    * Actividades Instaladas (Installed activities)
    * Diaro (Journal Activity)
"""

import os
import re
import sys
import json
import time
import sched
import logging
import sqlite3
import datetime
import traceback
import subprocess
import multiprocessing

__author__ = "Samuel Gutierrex <search.sama@gmail.com>"
__version__ = "1.0.1"

# Constants
MONDAY = 0
FRIDAY = 4
START_DAY_TIME = datetime.time(6, 0)
END_DAY_TIME = datetime.time(18, 0)
DB_NAME = "main.db"
JOURNAL_METADATA_DIR = "~/.sugar/default/datastore/"

# Logging setting
logger = logging.getLogger("xark")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)-s - %(message)s")
handler = logging.FileHandler(filename="xark.log", mode="a")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def getCurrentDayOfWeek(format=None):
    dayOfWeek = datetime.datetime.now().weekday()
    if format is not None:
        return dayOfWeek.strftime(format)

    return dayOfWeek


def getCurrentTime(format=None):
    dayTime = datetime.datetime.now().time()
    if format is not None:
        return dayTime.strftime(format)

    return dayTime


class Conexion:
    """Connection to SQLite DB"""

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.c = self.conn.cursor()

    def get(self, queryString, dataList):
        return self.c.execute(queryString, dataList).fetchone()

    def getmany(self, queryString, dataList):
        return self.c.execute(queryString, dataList).fetchall()

    def set(self, queryString, dataList):
        self.c.execute(queryString, dataList)
        self.conn.commit()

        return self.c.lastrowid

    def setmany(self, queryString, dataList):
        self.c.executemany(queryString, dataList)
        self.conn.commit()

    def close(self):
        self.c.close()
        self.conn.close()


class Xark:
    """XARK Class - Get data from XO laptop"""

    def __init__(self):
        # DB Connection
        self.db = Conexion()
        # Get status date print (integer current date)
        self.day = int(datetime.datetime.now().strftime("%Y%m%d"))
        # Get the laptop ID (laptio serial number)
        id = self.getSerial()
        self.serialnum = id["serialnum"]
        self.uuid = id["uuid"]
        # Check kaibil daily status
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

        # Journal metadata directory
        self.work_dir = JOURNAL_METADATA_DIR
        # Request Frequency Scheduler
        self.s = sched.scheduler(time.time, time.sleep)

    def getDailyId(self):
        """Get daily ID from DB if exist.

        Returns:
            int: Daily status id."""
        response = self.db.get(
            "SELECT id_status FROM xk_status WHERE date_print = ?", [(self.day)],
        )

        return int(response[0])

    def getSerial(self):
        """Get Serial Number and UUID

        Returns:
            dict: A dict with Serial Number and UUID on it."""
        data = dict()
        file = open("/home/.devkey.html", "r")

        def geyDevkeyPosition(self, devkey, index):
            return devkey[index].split("=")[1].replace('"', "")

        for value in file:
            if "serialnum" in value or "uuid" in value:
                value = value.strip().split(" ")
                data[geyDevkeyPosition(value, 2)] = geyDevkeyPosition(value, 3)

        return data

    def addFirst(self, data, item):
        """Add item to tuple at beginning of tuple.
        Args:
            data (tuple): Tuple to the item is added.
            item (str): Element to added at tuple.
        Returns:
            tuple: Tuple with the item added at beginning.
        """
        tmpList = list(data)
        tmpList.insert(0, item)

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
            file = open("{}/metadata/{}".format(file_dir, file_name), "r")
            contents = file.read()
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
            info = tuple(map(lambda x: self.readFile(in_dir[0].strip(), x), data_name))
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
        arch = arch + re.sub(r"\s+", " ", salida[13].strip()).split(":")[1].strip()

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
            "SELECT collect_status FROM xk_status WHERE date_print = ?", [(self.day)],
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
            "SELECT COUNT(*) FROM xk_data_xo WHERE xark_status_id = ?", [(self.dayid)],
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

        response = self.db.get(
            "SELECT sync_status, collect_status FROM xk_status WHERE date_print = ?",
            [(self.day)],
        )
        if bool(int(response[0])) and bool(int(response[1])):
            # Termina la funcion si ya se a sincronizacion con el charco
            return bool(int(response[0]))

        # Verifica si el IIAB esta disponible
        code = subprocess.Popen(
            'curl -o /dev/null -s -w "%{http_code}\n" ' + server,
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()
        code = int(code[0].strip())
        if code == 200 and bool(int(response[1])):
            data = dict()
            data["user"] = "olpc"
            data["client"] = self.getSerial()

            journal = self.db.getmany(
                "SELECT activity, activity_id, checksum, creation_time, file_size, icon_color, keep, launch_times, mime_type, mountpoint, mtime, share_scope, spent_times, time_stamp, title, title_set_by_user, uid FROM xk_journal_xo WHERE xark_status_id = ?",
                [(self.dayid)],
            )
            if journal is not None:
                data["journal"] = list(list(i.encode() for i in x) for x in journal)
            else:
                data["journal"] = list(list(map("Empty", range(17))))

            device = self.db.getmany(
                "SELECT activities_history, ram, rom, kernel, arqc, mac FROM xk_data_xo WHERE xark_status_id = ?",
                [(self.dayid)],
            )
            if device is not None:
                data["device"] = list(list(i.encode() for i in x) for x in device)
            else:
                data["journal"] = list(list(map("Empty", range(6))))

            request_url = (
                'curl -o /dev/null -w "%{http_code}\\n" '
                + '-H "Content-type: application/json" -X POST '
                + server
                + "data -d '"
                + json.dumps(data)
                + "'"
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
        "INSERT INTO xk_excepts(except_type, except_messg, file_name, file_line, except_code, tb_except, user_name, server_name) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (except_type.replace("'", '"')),
            (str(except_message).replace("'", '"')),
            (file_name.replace("'", '"')),
            (file_line.replace("'", '"')),
            (except_code.replace("'", '"')),
            (str(tb_except).replace("'", '"')),
            (os.environ["USER"].replace("'", '"')),
            (os.uname()[1].replace("'", '"')),
        ],
    )

    return True


if __name__ == "__main__":
    """Main flow of execution."""

    # Daily Start Log
    logger.info(
        "{} - start execution.".format(getCurrentDayOfWeek("%B %d %Y %A %H:%M:%S"))
    )

    try:
        # Kaibil Instance
        xark = Xark()

        if getCurrentDayOfWeek() >= MONDAY and getCurrentDayOfWeek() <= FRIDAY:
            if getCurrentTime() >= START_DAY_TIME and getCurrentTime() <= END_DAY_TIME:
                # Collect information
                multiprocessing.Process(target=xark.collection, args=()).start()
                # Synchronize puddle
                multiprocessing.Process(target=xark.synchrome, args=()).start()

                # Close Connection
                Conexion().close()
            else:
                logger.info(
                    "Time of day {} out of range 6:00 to 18:00.".format(
                        getCurrentTime("%H:%M:%S")
                    )
                )
        else:
            logger.info(
                "Day of the week {} not Monday through Friday.".format(
                    getCurrentDayOfWeek("%A")
                )
            )
    except Exception() as e:
        logger.error("Exception: {}".format(e))
        print(e)
        cath_Exception(e)
        sys.exit(1)
