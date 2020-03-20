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
import time
import json
import sched
import values
import public
import sqlite3
import logging
import datetime
import traceback
import subprocess
import multiprocessing

__author__ = "Samuel Gutierrez <search.sama@gmail.com>"
__credits__ = ["Samuel Gutierrez", "Nestor Bonilla", "Porfirio Paiz"]
__email__ = "search.sama@gmail.com"
__license__ = "Apache License"
__maintainer__ = "Samuel Gutierrez"
__status__ = "Development"
__version__ = "1.0.1"

# Constants
FRIDAY = 4
MONDAY = 0
APP_NAME = "XARK"
ROOT_POSITION = 0
FIRST_POSITION = 1
SECOND_POSITION = 2
DB_NAME = "main.db"
XO_CONFIG_FILE = "config.json"
END_DAY_TIME = datetime.time(18, 0)
START_DAY_TIME = datetime.time(6, 0)
DEVELOP_ID_FILE = "/home/.devkey.html"
JOURNAL_METADATA_DIR = "~/.sugar/default/datastore/"

# Queries
INSER_INTO_XK_DATA_OX = "INSERT INTO xk_data_xo(xark_status_id, activities_history, ram, rom, kernel, arqc, mac) VALUES(?, ?, ?, ?, ?, ?, ?)"
INSER_INTO_XK_JOURNAL_XO = "INSERT INTO xk_journal_xo(xark_status_id, activity, activity_id, checksum, creation_time, file_size, icon_color, keep, launch_times, mime_type, mountpoint, mtime, share_scope, spent_times, time_stamp, title, title_set_by_user, uid) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
INSERT_INTO_XK_EXCPTS = "INSERT INTO xk_excepts(except_type, except_messg, file_name, file_line, except_code, tb_except, user_name) VALUES(?, ?, ?, ?, ?, ?, ?)"
INSERT_INTO_XK_STATUS = (
    "INSERT INTO xk_status(serial_num, uuid, date_print) VALUES(?, ?, ?)"
)
SELECT_COLLECT_STATUS = "SELECT collect_status FROM xk_status WHERE date_print = ?"
SELECT_COUNT_DATA = "SELECT COUNT(*) FROM xk_data_xo WHERE xark_status_id = ?"
SELECT_COUNT_JOURNAL = "SELECT COUNT(*) FROM xk_journal_xo WHERE xark_status_id = ?"
SELECT_DAILY_DATEPRINT = "SELECT id_status FROM xk_status WHERE date_print = ?"
SELECT_DATA_STATUS = "SELECT date_print, collect_status, collect_date, create_at, update_at FROM xk_status WHERE id_status = ?"
SELECT_DEVICE_DATA = "SELECT activities_history, ram, rom, kernel, arqc, mac, create_at, update_at FROM xk_data_xo WHERE xark_status_id = ?"
SELECT_EXCEPTIONS_DATA = "SELECT except_type, except_messg, file_name, file_line, except_code, tb_except, user_name, create_at, update_at FROM xk_excepts WHERE ?"
SELECT_JOURNAL_DATA = "SELECT activity, activity_id, checksum, creation_time, file_size, icon_color, keep, launch_times, mime_type, mountpoint, mtime, share_scope, spent_times, time_stamp, title, title_set_by_user, uid, create_at, update_at FROM xk_journal_xo WHERE xark_status_id = ?"
SELECT_SYNC_STATUS = (
    "SELECT sync_status, collect_status FROM xk_status WHERE date_print = ?"
)
UPDATE_STATUS_COLLECT = (
    "UPDATE xk_status set collect_status = ?, collect_date = ? WHERE date_print = ?"
)
UPDATE_SYNC_STATUS = (
    "UPDATE xk_status set sync_status = ?, sync_date = ? WHERE date_print = ?"
)

# Logging setting
logger = logging.getLogger(APP_NAME.lower())
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)-s - %(message)s")
handler = logging.FileHandler(filename=APP_NAME.lower() + ".log", mode="a")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def getCurrentDayOfWeek(format=None):
    dayOfWeek = datetime.datetime.now()
    if format is not None:
        return dayOfWeek.strftime(format)

    return dayOfWeek.weekday()


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


def parse(self, line):
    """Parse line and return a dictionary with variable value"""
    if line.lstrip().startswith("#"):
        return {}

    if not line.lstrip():
        return {}

    """find the second occurence of a quote mark:"""
    if line.find("export=") == 0:
        line = line.replace("export=", "")

    quote_delimit = max(
        line.find("'", line.find("'") + 1), line.find('"', line.rfind('"')) + 1
    )

    """find first comment mark after second quote mark"""
    if "#" in line:
        line = line[: line.find("#", quote_delimit)]

    key, value = map(lambda x: x.strip().strip("'").strip('"'), line.split("=", 1))

    return {key: value}


class EnvFile(dict):
    """.env file class"""

    path = None

    def __init__(self, path, **kwargs):
        self.path = os.path.abspath(os.path.expanduser(path))
        if os.path.exists(self.path):
            for line in open(self.path).read().splitlines():
                self.update(parse(line))

        for k, v in kwargs.items():
            self[k] = v

    def load(self):
        os.environ.update(self)

    def save(self):
        """save a dictionary to a file"""
        lines = []

        for key, value in self.items():
            lines.append("%s=%s" % (key, value))

        lines.append("")
        open(self.path, "w").write("\n".join(lines))

    def __setitem__(self, key, value):
        super(EnvFile, self).__setitem__(key, value)

    def __delitem__(self, key):
        super(EnvFile, self).__delitem__(key)


def get(path=".env"):
    """return a dictionary wit .env file variables"""
    data = dict()

    if not path:
        path = ".env"

    for path in values.get(path):
        if not os.path.exists(path):
            raise OSError("%s NOT EXISTS" % os.path.abspath(path))

        data.update(EnvFile(path))

    return data


def load(path=".env"):
    """set environment variables from .env file"""
    if not path:
        path = ".env"

    for path in values.get(path):
        path = os.path.abspath(os.path.expanduser(path))

        if not os.path.exists(path):
            raise OSError("%s NOT EXISTS" % path)

        os.environ.update(get(path))


class Xark:
    """
    Xark class for extract device info from xo laptop.

    Methods:
        addOnFirstPosition()
        collection()
        extracData()
        extracExcepts()
        extracJournal()
        extracLogs()
        getActivityHistory()
        getArch()
        getDailyId()
        getDayPrint()
        getFileContent()
        getKernel()
        getMac()
        getRam()
        getRom()
        getXOIdentifier()
        readFile()
        synchrome()
    """

    def __init__(self, serverName, userName, networkIface, workingDir):
        # DB Connection class
        self.db = Conexion()
        # Get status day print (integer current date)
        self.day = self.getDayPrint()
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

    def getDayPrint(self):
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

        def geyDevKeyValue(devkeyTag, index):
            return devkeyTag[index].split("=")[FIRST_POSITION].replace('"', "")

        for tag in file:
            if "serialnum" in tag or "uuid" in tag:
                tag = tag.strip().split(" ")
                dataDict[geyDevKeyValue(tag, 2)] = geyDevKeyValue(tag, 3)

        return dataDict

    def addOnFirstPosition(self, tupleData, newItem):
        """Add item to tuple at beginning of tuple.

        Args:
            newItem (str): Element to added at tuple.
            tupleData (tuple): Tuple to the item is added.

        Returns:
            tuple: Tuple with the item added at beginning.
        """
        tmpList = list(tupleData)
        tmpList.insert(ROOT_POSITION, newItem)

        return tuple(tmpList)

    def readFile(self, filePath, fileName):
        """Read the metadata file content.

        Args:
            fileName (str): File name to read.
            filePath (str): Path to the metadata directory.

        Returns:
            dict: (File Name, File Content).
        """
        file = None
        if os.path.isfile("{}/metadata/{}".format(filePath, fileName)):
            file = open("{}/metadata/{}".format(filePath, fileName), "r").read()
            if file is None or file == "":
                return "Empty"
        else:
            return "Empty"

        return file

    def getFileContent(self, fullFilePath):
        """List each existing file in the metadata directory.

        Args:
            fullFilePath (str): Path to the metadata directory.

        Returns:
            list: List of dictionary contents.
        """
        journalFiles = [
            "activity_id",
            "activity",
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
            "title_set_by_user",
            "title",
            "uid",
        ]

        if fullFilePath not in [
            "checksums",
            "ds_clean",
            "index_updated",
            "index",
            "version",
        ]:
            onDir = subprocess.Popen(
                "ls -d {}{}/*".format(self.journalDir, fullFilePath),
                shell=True,
                stdout=subprocess.PIPE,
            ).stdout.readlines()
            fileContent = tuple(
                map(
                    lambda file: self.readFile(
                        onDir[ROOT_POSITION].strip().decode(), file
                    ),
                    journalFiles,
                )
            )

            return self.addOnFirstPosition(fileContent, self.dayId)

        return None

    def extracJournal(self):
        """Extract diary metadata information.

        Returns:
            list: List of contents of each metadata file.
        """
        fileList = subprocess.Popen(
            "ls {}".format(self.journalDir), shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        fileList = list(file.strip().decode() for file in fileList)
        infoPerFile = map(lambda file: self.getFileContent(file), fileList)
        infoPerFile = list(filter(lambda fileInfo: fileInfo, infoPerFile))

        return infoPerFile

    def getActivityHistory(self):
        """Extract activity history information.

        Returns:
            str: History content.
        """
        historyContent = ""
        activityList = subprocess.Popen(
            "ls {}Activities/".format(self.workingDir),
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()
        amount = len(activityList) - 1

        return ",".join(
            list(
                activity
                for activity in activityList
                if activityList.index(activity) < amount
            )
        )

    def getRam(self):
        """Get RAM mesure.

        Returns:
            str: RAM mesure on bytes.
        """
        memAmount = ""
        freeOutput = subprocess.Popen(
            "free -m", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        freeOutput = list(cell.strip().decode() for cell in freeOutput)
        ramValuesList = re.sub(r"\s+", " ", freeOutput[FIRST_POSITION])
        swapValuesList = re.sub(r"\s+", " ", freeOutput[SECOND_POSITION])

        def concatIterator(iteratorList):
            concatChain = iteratorList.strip().split(" ")
            concatChain = list(
                filter(
                    lambda item: concatChain.index(item) > 0
                    and concatChain.index(item) <= 3,
                    concatChain,
                )
            )
            amount = len(concatChain) - 1

            return ",".join(
                list(
                    shackle
                    for shackle in concatChain
                    if concatChain.index(shackle) < amount
                )
            )

        memAmount = concatIterator(ramValuesList)
        memAmount = memAmount + "|"
        memAmount = memAmount = concatIterator(swapValuesList)

        return memAmount

    def getRom(self):
        """Get ROM mesure.

        Returns:
            str: ROM mesure on bytes.
        """
        diskSpace = ""
        dfOutput = subprocess.Popen(
            "df -H --output=source,size,used,avail,target",
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()
        for column in dfOutput:
            field = re.sub(r"\s+", " ", column.strip().decode()).split(" ")
            if "/dev/" in field[0]:
                field = list(
                    filter(
                        lambda item: field.index(item) > 0 and field.index(item) <= 4,
                        field,
                    )
                )
                amount = len(field) - 1
                diskSpace = ",".join(
                    list(item for item in field if field.index(item) < amount)
                )
                diskSpace = diskSpace + "|"

        return diskSpace[:-1]

    def getKernel(self):
        """Get Kernel settings.

        Returns:
            str: Kernel settings.
        """
        kernel = subprocess.Popen(
            "uname -a", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()

        return kernel[ROOT_POSITION].strip().decode().split("#")[ROOT_POSITION].strip()

    def getArch(self):
        """Get system architecture

        Returns:
            str: Architecture system settings.
        """
        arch = ""
        lscpuOutput = subprocess.Popen(
            "lscpu", shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        arch = (
            arch
            + re.sub(r"\s+", " ", lscpuOutput[0].strip().decode()).split(" ")[
                FIRST_POSITION
            ]
        )
        arch = arch + "|"
        arch = (
            arch
            + re.sub(r"\s+", " ", lscpuOutput[4].strip().decode()).split(" ")[
                FIRST_POSITION
            ]
        )
        arch = arch + "|"
        arch = (
            arch
            + re.sub(r"\s+", " ", lscpuOutput[13].strip().decode())
            .split(":")[FIRST_POSITION]
            .strip()
        )

        return arch

    def getMac(self):
        """Get network computer MAC address

        Returns:
            str: MAC address
        """
        mac = subprocess.Popen(
            "cat /sys/class/net/{}/address".format(self.networkIface),
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()

        return mac[ROOT_POSITION].strip().decode()

    def extracData(self):
        """Extract data from computer

        Returns:
            tuple: Computer data.
        """
        data = list()
        data.append(self.getActivityHistory())
        data.append(self.getRam())
        data.append(self.getRom())
        data.append(self.getKernel())
        data.append(self.getArch())
        data.append(self.getMac())
        data.insert(0, self.dayId)

        return tuple(data)

    def extracLogs(self):
        print(True)

        return True

    def extracExcepts(self):
        print(True)

        return True

    def collection(self):
        """Collect information from the laptop xo.

        Returns:
            bool: True/False.
        """
        status = self.db.get(SELECT_COLLECT_STATUS, [(self.day)])[ROOT_POSITION]
        if bool(int(status)):
            # The information for the day has already been collected.
            return bool(int(status))

        # Extract information from the newspaper.
        journal = self.extracJournal()
        self.db.setmany(
            INSER_INTO_XK_JOURNAL_XO, journal,
        )
        # Extract device information
        data = self.extracData()
        self.db.set(
            INSER_INTO_XK_DATA_OX, data,
        )

        journalCount = self.db.get(SELECT_COUNT_JOURNAL, [(self.dayId)],)
        dataCount = self.db.get(SELECT_COUNT_DATA, [(self.dayId)],)
        if int(journalCount[ROOT_POSITION]) >= 1 and int(dataCount[ROOT_POSITION]) >= 1:
            # Synchronization status in `Synchronized`
            self.db.set(
                UPDATE_STATUS_COLLECT, [(True), (datetime.datetime.now()), (self.day)],
            )

            return True
        else:
            return False

    def synchrome(self):
        """Synchronize with the puddle."""

        syncStatus = self.db.get(SELECT_SYNC_STATUS, [(self.day)],)
        if bool(int(syncStatus[ROOT_POSITION])) and bool(
            int(syncStatus[FIRST_POSITION])
        ):
            # The function ends if it is already synchronized with the puddle
            return bool(int(syncStatus[ROOT_POSITION]))

        # Check if the IIAB is available
        requestUrl = (
            'curl -o /dev/null -w "%{http_code}\\n" -X POST '
            + self.serverName
            + ' -d "user='
            + self.userName
            + "&client_id="
            + self.serialNumber
            + "&client_secret="
            + self.uuid
            + '"'
        )
        code = subprocess.Popen(
            requestUrl, shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        code = int(code[ROOT_POSITION].strip().decode())

        if code == 200 and bool(int(syncStatus[FIRST_POSITION])):
            data = dict()
            status = self.db.get(SELECT_DATA_STATUS, [(self.dayId)],)
            if status is not None:
                data["status"] = list(str(item).encode() for item in status)
            else:
                data["status"] = list(list(map("Empty", range(5))))

            journal = self.db.getmany(SELECT_JOURNAL_DATA, [(self.dayId)],)
            if journal is not None:
                data["journal"] = list(
                    list(str(item).encode() for item in field) for field in journal
                )
            else:
                data["journal"] = None

            device = self.db.get(SELECT_DEVICE_DATA, [(self.dayId)],)
            if device is not None:
                data["device"] = list(str(item).encode() for item in device)
            else:
                data["device"] = None

            excepts = self.db.getmany(SELECT_EXCEPTIONS_DATA, [(1)],)
            if excepts is not None:
                data["excepts"] = list(
                    list(str(i).encode() for i in x) for x in excepts
                )
            else:
                data["excepts"] = None

            requestUrl = (
                "curl -u "
                + self.serialNumber
                + ":"
                + self.uuid
                + ' -o /dev/null -w "%{http_code}\\n" -X POST '
                + self.serverName
                + "data -d "
                + '"grant_type=password&username='
                + self.userName
                + "&client="
                + self.serialNumber
                + '&password=valid&scope=profile&data={}"'.format(data)
            )
            curlOutput = subprocess.Popen(
                requestUrl, shell=True, stdout=subprocess.PIPE
            ).stdout.readlines()
            curlOutput = int(curlOutput[ROOT_POSITION].strip().decode())

            if curlOutput == 200:
                self.db.set(
                    UPDATE_SYNC_STATS, [(True), (datetime.datetime.now()), (self.day)],
                )
                return True
        else:
            self.scheduler.enter(10, 1, self.synchrome, ())
            self.scheduler.run()


def cath_Exception(tbExcept):
    """Capture traceback and exceptions to save in xark_except.
    Args:
        tbExcept (str): Excepcion.
    """
    # Type of the exception.
    exceptType = str(sys.exc_info()[ROOT_POSITION])
    exceptType = exceptType.split("'")[FIRST_POSITION]
    # Exception message.
    exceptMessage = sys.exc_info()[FIRST_POSITION]
    # Capture traceback
    tb = sys.exc_info()[SECOND_POSITION]
    tbInfo = traceback.format_tb(tb)[len(traceback.format_tb(tb)) - FIRST_POSITION]
    # Script Name
    fileName = tbInfo.split(",")[ROOT_POSITION].strip()
    # Exception line.
    fileLine = tbInfo.split(",")[FIRST_POSITION].strip()
    # Excerpt code snippet.
    exceptCode = tbInfo.split(",")[SECOND_POSITION].strip()

    Conexion().set(
        INSERT_INTO_XK_EXCPTS,
        [
            (exceptType.replace("'", '"')),
            (str(exceptMessage).replace("'", '"')),
            (fileName.replace("'", '"')),
            (fileLine.replace("'", '"')),
            (exceptCode.replace("'", '"')),
            (str(tbExcept).replace("'", '"')),
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
