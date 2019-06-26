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
    def __init__(self):
        self.conn = sqlite3.connect("main.db")
        self.c = self.conn.cursor()

    def get(self, query, data):
        return self.c.execute(query, data).fetchone()

    def set(self, query, data):
        self.c.execute(query, data)
        self.conn.commit()

        return self.c.lastrowid

    def setmany(self, query, data):
        self.c.executemany(query, data)
        self.conn.commit()

    def close(self):
        self.c.close()
        self.conn.close()


class Xark:
    def __init__(self):
        self.db = Conexion()
        # Fecha actual en entero
        self.day = int(datetime.datetime.now().strftime("%Y%m%d"))
        # Obtenr el identificador de la laptop
        id = self.getSerialNumber()
        self.serialnum = id["serialnum"]
        self.uuid = id["uuid"]
        # Verificar estado diario del kaibil
        response = self.db.get(
            "SELECT * FROM xk_status WHERE date_print = ?", [(self.day)]
        )
        # print(response)
        if response is None:
            self.dayid = self.db.set(
                "INSERT INTO xk_status(serial_num, uuid, date_print) VALUES(?, ?, ?)",
                [(self.serialnum), (self.uuid), (self.day)],
            )

        # Directorio de metadata del Diario
        self.work_dir = "~/.sugar/default/datastore/"
        # Programador de frecuencia de peticiones
        self.s = sched.scheduler(time.time, time.sleep)

    def getSerialNumber(self):
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

    def read_file(self, file_dir, file_name):
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
            if contents is None:
                contents = "Empty"
        else:
            contents = "Empty"

        return contents

    def get_info_journal(self, dir):
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
            "launch-times",
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
                map(
                    lambda x: self.read_file(in_dir[0].strip(), x)
                    if x in data_name
                    else False,
                    data_name,
                ),
            )
            print(info[0])
            return info

    def extrac_journal(self):
        """Lee y extrae la informacion de metadata del diaro.
        Returns:
            list: Lista de contenidos de cada archivo de metadata.
        """
        salida = subprocess.Popen(
            "ls {}".format(self.work_dir), shell=True, stdout=subprocess.PIPE
        ).stdout.readlines()
        salida = list(x.strip() for x in salida)
        info = map(lambda x: self.get_info_journal(x), salida)
        info = filter(lambda x: x, info)
        return info

    def collection(self):
        """Recolectar informacion de la laptop xo.
        Returns:
            bool: True/False.
        """
        response = self.db.get(
            "SELECT collect_status FROM xk_status WHERE date_print = ?",
            [(self.day)],
        )
        if int(response[0]):
            # La informacion para el dia ya se ha rocolectado.
            # Termina la funcion.
            return bool(int(response[0]))

        # Extraer informacion del diario y guadarlo en la base de datos.
        journal = self.extrac_journal()
        # print(journal)
        self.db.setmany(
            "INSERT INTO xk_journal_xo(xark_status_id, activity, activity_id, checksum, creation_time, file_size, icon_color, keep, launch_times, mime_type, mountpoint, mtime, share_scope, spent_times, time_stamp, title, title_set_by_user, uid) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            journal,
        )
        # Estado de sincronizacion en `Sincronizado`
        # self.db.set(
        #     "UPDATE xk_status set collect_status = ?, collect_date = ? WHERE date_print = ?",
        #     [(True), (datetime.datetime.now()), (self.day)],
        # )

    def synchrome(self):
        """Sincronizar con el charco."""
        response = self.db.get(
            "SELECT sync_status FROM xk_status WHERE date_print=?",
            [(self.day)],
        )
        if not response[0]:
            # Termina la funcion si ya se a sincronizacion con el charco
            return bool(response[0])

        # Verifica si el IIAB esta disponible
        code = subprocess.Popen(
            'curl -o /dev/null -s -w "%{http_code}\n" http://10.0.11.33:5000/',
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()
        code = int(code[0].strip())

        if code == 200:
            url = "http://10.0.11.33:5000/"
            result = subprocess.Popen(
                'curl -o /dev/null -s -w "%{http_code}\n" ' + url,
                shell=True,
                stdout=subprocess.PIPE,
            ).stdout.readlines()
            result = int(result[0].strip())
            if code == 200:
                self.db.set(
                    "UPDATE xk_status set sync_status = ?, sync_date = ? WHERE date_print = ?",
                    [(True), (datetime.datetime.now()), (self.day)],
                )
                return True
        else:
            self.s.enter(10, 1, self.synchrome, ())
            self.s.run()

    def cath_Exception(self, tb_except):
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

        self.db.set(
            "INSERT INTO xk_excepts(except_type, except_messg, file_name, file_line, code_snipe, tb_except, user_name, server_name) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (except_type),
                (except_message),
                (file_name),
                (file_line),
                (except_code),
                (tb_except),
                (os.environ["USER"]),
                (os.uname()[1]),
            ],
        )

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
            ) and datetime.datetime.now().time() <= datetime.time(19,  0):
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
                # sys.exit(1)
        else:
            logger.info(
                "Dia de la semana {} no de lunes a viernes".format(
                    datetime.datetime.now().weekday()
                )
            )
            # sys.exit(1)
    except:
        logger.error("Exception: {}".format(" "))
        Xark().cath_Exception(" ")
        # sys.exit(1)
