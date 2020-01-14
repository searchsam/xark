#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""XO Agil Recolector Kaibil - XARK

Internal information collector of the XO. Currently collects:
    * Installed Activities
    * Journal Activity Metadata
    * Kernel
    * MAC
    * Procesor Architecture
    * RAM
    * ROM
    * Serial Number
    * UUID
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

__author__ = "Samuel Gutierrez <search.sama@gmail.com>"
__credits__ = ["Samuel Gutierrez", "Nestor Bonilla", "Porfirio Paiz"]
__license__ = "Apache License"
__version__ = "1.0.1"
__maintainer__ = "Samuel Gutierrez"
__email__ = "search.sama@gmail.com"
__status__ = "Development"

# Constants
MONDAY = 0
FRIDAY = 4
START_DAY_TIME = datetime.time(6, 0)
END_DAY_TIME = datetime.time(18, 0)
DB_NAME = "main.db"
XO_CONFIG_FILE = "config.json"
JOURNAL_METADATA_DIR = "~/.sugar/default/datastore/"
APP_NAME = "XARK"
DEVELOP_ID_FILE = "/home/.devkey.html"
ROOT_POSITION = 0
FIRST_POSITION = 1

# Queries
SELECT_DAILY_DATEPRINT = "SELECT id_status FROM xk_status WHERE date_print = ?"
INSERT_INTO_XK_STATUS = (
    "INSERT INTO xk_status(serial_num, uuid, date_print) VALUES(?, ?, ?)"
)

# Logging setting
logger = logging.getLogger(APP_NAME.lower())
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)-s - %(message)s")
handler = logging.FileHandler(filename=APP_NAME.lower() + "log", mode="a")
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
        addOnFirstPos()
        collection()
        extracData()
        extracExcepts()
        extracJournal()
        extracLogs()
        getActivityHistory()
        getArch()
        getDailyId()
        getFileContent()
        getMac()
        getRam()
        getRom()
        getXOIdentifier()
        getKernel()
        readFile(self, file_dir, file_name)
        synchrome()
    """

    def __init__(self, serverName, userName, networkIface, workingDir):
        # DB Connection class
        self.db = Conexion()
        # Get status date print (integer current date)
        self.day = getDatePrint()
        # Get Laptop identifier
        id = self.getXOIdentifier()
        self.serialNumber = id["serialnum"]
        self.uuid = id["uuid"]
        # Check kaibil daily status
        self.dayId = None
        response = self.db.get(SELECT_DAILY_DATEPRINT, [(self.day)])

        if response is None:
            self.dayId = self.db.set(
                INSERT_INTO_XK_STATUS, [(self.serialNumber), (self.uuid), (self.day)],
            )
        else:
            self.dayId = self.getDailyId()

        # Directorio de metadata del Diario
        self.journalDir = workingDir + ".sugar/default/datastore/"
        # Indentificacion del servidor
        self.serverName = serverName
        self.userName = userName
        self.networkIface = networkIface
        self.workingDir = workingDir
        # Request Frequency Scheduler
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def getDatePrint(self):
        """Get the date of current day on int.

        Returns:
            int: Date on int."""
        return int(datetime.datetime.now().strftime("%Y%m%d"))

    def getDailyId(self):
        """Get daily ID from DB if exist.

        Returns:
            int: Daily status id."""
        response = self.db.get(SELECT_DAILY_DATEPRINT, [(self.day)],)

        return int(response[ROOT_POSITION])

    def getXOIdentifier(self):
        """Get Serial Number and UUID.

        Returns:
            dict: A dict with Serial Number and UUID on it."""
        dataDict = dict()
        file = open(DEVELOP_ID_FILE, "r")

        def geyDevKeyValue(self, devkeyTag, index):
            return devkeyTag[index].split("=")[FIRST_POSITION].replace('"', "")

        for tag in file:
            if "serialnum" in tag or "uuid" in tag:
                tag = tag.strip().split(" ")
                dataDict[geyDevKeyValue(tag, 2)] = geyDevKeyValue(tag, 3)

        return dataDict

    def addOnFirstPosition(self, tupleData, newItem):
        """Add item to tuple at beginning of tuple.

        Args:
            tupleData (tuple): Tuple to the item is added.
            newItem (str): Element to added at tuple.

        Returns:
            tuple: Tuple with the item added at beginning.
        """
        tmpList = list(tupleData)
        tmpList.insert(ROOT_POSITION, newItem)

        return tuple(tmpList)

    def readFile(self, filePath, fileName):
        """Read the metadata file content.

        Args:
            filePath (str): Path to the metadata directory.
            fileName (str): File name to read.

        Returns:
            dict: (File Name, File Content).
        """
        contents = ""
        if os.path.isfile("{}/metadata/{}".format(filePath, fileName)):
            file = open("{}/metadata/{}".format(filePath, fileName), "r")
            contents = file.read()
            if contents is None or contents == "":
                contents = "Empty"
        else:
            contents = "Empty"

        return contents

    def getFileContent(self, fullFilePath):
        """List each existing file in the metadata directory.

        Args:
            fullFilePath (str): Path to the metadata directory.

        Returns:
            list: List of dictionary contents.
        """
        journalFiles = [
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

        if fullFilePath not in [
            "index",
            "checksums",
            "index_updated",
            "version",
            "ds_clean",
        ]:
            onDir = subprocess.Popen(
                "ls -d {}{}/*".format(self.journalDir, fullFilePath),
                shell=True,
                stdout=subprocess.PIPE,
            ).stdout.readlines()
            fileContent = tuple(
                map(
                    lambda file: self.readFile(onDir[ROOT_POSITION].strip(), file),
                    journalFiles,
                )
            )
            fileContent = self.addFirst(fileContent, self.dayId)

            return fileContent

        return None

    def extracJournal(self):
        """Extract diary metadata information.

        Returns:
            list: List of contents of each metadata file.
        """
        fileList = subprocess.Popen(
            "ls {}".format(self.journalDir), shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        fileList = list(file.strip() for file in fileList)
        infoPerFile = map(lambda file: self.getFileContent(file), fileList)
        infoPerFile = filter(lambda fileInfo: fileInfo, infoPerFile)

        return infoPerFile

    def getActivityHistory(self):
        """extra activity history information.

        Returns:
            str: History content.
        """
        historyContent = ""
        activitiesList = subprocess.Popen(
            "ls {}Activities/".format(self.workingDir),
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()
        for enumerator, activity in enumerate(activitiesList):
            if enumerator < len(activitiesList) - 1:
                historyContent += activity.strip() + ","
            else:
                historyContent += activity.strip()

        return historyContent

    def getRam(self):
        Memory = ""
        freeOutput = subprocess.Popen(
            "free -m", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        ramValuesList = re.sub(r"\s+", " ", freeOutput[1])
        swapValuesList = re.sub(r"\s+", " ", freeOutput[2])

        def concatIterator(self, iteratorList):
            concatChain = Memory
            for enumerator, concatValue in enumerate(iteratorList.strip().split(" ")):
                if enumerator > 0 and enumerator <= 3:
                    if enumerator < 3:
                        concatChain = concatChain + concatValue + ","
                    else:
                        concatChain = concatChain + concatValue

            return concatChain

        Memory = concatIterator(ramValuesList)
        Memory = Memory + "|"
        Memory = concatIterator(swapValuesList)

        return Memory

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
        kernel = kernel[ROOT_POSITION].strip().split("#")[ROOT_POSITION].strip()
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
        mac = subprocess.Popen(
            "cat /sys/class/net/{}/address".format(self.iface),
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

    def extracExcepts(self):
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

        # Extraer informacion del diario.
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
            + self.server
            + ' -d "user='
            + self.user
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

            status = self.db.get(
                "SELECT date_print, collect_status, collect_date, create_at, update_at FROM xk_status WHERE id_status = ?",
                [(self.dayid)],
            )
            if status is not None:
                data["status"] = list(str(i).encode() for i in status)
            else:
                data["status"] = list(list(map("Empty", range(5))))

            journal = self.db.getmany(
                "SELECT activity, activity_id, checksum, creation_time, file_size, icon_color, keep, launch_times, mime_type, mountpoint, mtime, share_scope, spent_times, time_stamp, title, title_set_by_user, uid, create_at, update_at FROM xk_journal_xo WHERE xark_status_id = ?",
                [(self.dayid)],
            )
            if journal is not None:
                data["journal"] = list(
                    list(str(i).encode() for i in x) for x in journal
                )
            else:
                data["journal"] = None

            device = self.db.get(
                "SELECT activities_history, ram, rom, kernel, arqc, mac, create_at, update_at FROM xk_data_xo WHERE xark_status_id = ?",
                [(self.dayid)],
            )
            if device is not None:
                data["device"] = list(str(i).encode() for i in device)
            else:
                data["device"] = None

            excepts = self.db.getmany(
                "SELECT except_type, except_messg, file_name, file_line, except_code, tb_except, user_name, create_at, update_at FROM xk_excepts WHERE ?",
                [(1)],
            )
            print(excepts)
            if excepts is not None:
                data["excepts"] = list(
                    list(str(i).encode() for i in x) for x in excepts
                )
            else:
                data["excepts"] = None

            request_url = (
                "curl -u "
                + self.serialnum
                + ":"
                + self.uuid
                + ' -o /dev/null -w "%{http_code}\\n" -X POST '
                + self.server
                + "data -d "
                + '"grant_type=password&username='
                + self.user
                + "&client="
                + self.serialnum
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
    """Main flow of execution."""

    # Daily Start Log
    logger.info(
        "{} - start execution.".format(getCurrentDayOfWeek("%B %d %Y %A %H:%M:%S"))
    )

    try:
        # Get the settings from config.json
        with open(XO_CONFIG_FILE) as config_file:
            config = json.load(config_file)

        # Kaibil Instance
        xark = Xark(config["host"], config["user"], config["iface"], config["w_dir"])

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

#    ___    ___ ________  ________  ___  __
#   |\  \  /  /|\   __  \|\   __  \|\  \|\  \
#   \ \  \/  / | \  \|\  \ \  \|\  \ \  \/  /|_
#    \ \    / / \ \   __  \ \   _  _\ \   ___  \
#     /     \/   \ \  \ \  \ \  \\  \\ \  \\ \  \
#    /  /\   \    \ \__\ \__\ \__\\ _\\ \__\\ \__\
#   /__/ /\ __\    \|__|\|__|\|__|\|__|\|__| \|__|
#   |__|/ \|__| Baby SAHRK hunting for device information without supervision.
