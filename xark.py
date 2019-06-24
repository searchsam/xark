#!/usr/bin/python

'''
XO Agil Recolector Kaibil - XARK

Recolector de informacion interno de la XO. Actualmentle solo recolecta:
    * Serial number
    * UUID
'''

import sys
import time
import sched
import logging
import sqlite3
import datetime
import subprocess
import multiprocessing

# Logging setting
logger = logging.getLogger('xark')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-s - %(message)s')
handler = logging.FileHandler(filename='xark.log', mode='a')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Conexion:
    def __init__(self):
        self.conn = sqlite3.connect('main.db')
        self.c = self.conn.cursor()

    def get(self, query, data):
        return self.c.execute(query, data).fetchone()

    def set(self, query, data):
        self.c.execute(query, data)
        self.conn.commit()

    def close(self):
        self.c.close()
        self.conn.close()


class Xark:
    def __init__(self):
        self.db = Conexion()
        # Fecha actual en entero
        self.day = int(datetime.datetime.now().strftime('%Y%m%d'))
        # Verificar estado diario del kaibil
        response = self.db.get(
            'SELECT * FROM xark_status WHERE date_print = ?',
            [(self.day)]
        )
        if response is None:
            self.db.set(
                'INSERT INTO xark_status(date_print) VALUES(?)',
                [(self.day)]
            )
        # Programador de frecuencia de peticiones
        self.s = sched.scheduler(time.time, time.sleep)

    def getSerialNumber(self):
        '''Capturar Numero de serie y UUID'''
        data = dict()
        f = open('/home/.devkey.html', 'r')
        for value in f:
            if 'serialnum' in value or 'uuid' in value:
                value = value.strip().split(' ')
                data[value[2].split('=')[1].replace('"', '')] = (
                    value[3].split('=')[1].replace('"', '')
                )

        return data

    def collection(self):
        '''Funcion para recolectar informacion'''
        response = self.db.get(
            'SELECT collect_status FROM xark_status WHERE date_print = ?',
            [(self.day)]
        )
        if not response[0]:
            # Termina la funcion ya se ha recolectado informacion
            return bool(response[0])

        data = self.getSerialNumber()
        self.db.set(
            'INSERT INTO data_xo(serial_num, uuid) VALUES(?, ?)',
            [(data['serialnum']), (data['uuid'])],
        )

        # Estado de sincronizacion en `Sincronizado`
        self.db.set(
            'UPDATE xark_status set collect_status = ?, collect_date = ? WHERE date_print = ?',
            [(True), (datetime.datetime.now()), (self.day)],
        )

    def synchrome(self):
        '''Funcion para sincronizar con el charco.'''
        response = self.db.get(
            'SELECT sync_status FROM xark_status WHERE date_print=?',
            [(self.day)]
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
            url = 'http://10.0.11.33:5000/'
            result = subprocess.Popen(
                'curl -o /dev/null -s -w "%{http_code}\n" ' + url,
                shell=True,
                stdout=subprocess.PIPE,
            ).stdout.readlines()
            result = int(result[0].strip())
            if code == 200:
                self.db.set(
                    'UPDATE xark_status set sync_status = ?, sync_date = ? WHERE date_print = ?',
                    [(True), (datetime.datetime.now()), (self.day)],
                )
                return True
        else:
            self.s.enter(10, 1, self.synchrome, ())
            self.s.run()


if __name__ == '__main__':
    # Log de inicio diario
    logger.info('Inicio de dia {}'.format(datetime.datetime.now()))
    # Lista de multiprocesos
    processes = list()
    try:
        # Instancia del Kaibil
        xark = Xark()

        # Verifica si el dia de la semana es entre lunes y viernes
        if (
            datetime.datetime.now().weekday() >= 1
            and datetime.datetime.now().weekday() <= 5
        ):
            # Verifica que la hora del dia sea entre las 6:00 y las 18:00
            if datetime.datetime.now().time() >= datetime.time(
                6, 0
            ) and datetime.datetime.now().time() <= datetime.time(18, 0):
                # Recolectar informacion
                multiprocessing.Process(target=xark.collection, args=()).start()
                # Sincronizar con el charco
                multiprocessing.Process(target=xark.synchrome, args=()).start()

                # close connection
                Conexion().close()
        else:
            exit('Fin de la ejecucion')
    except Exception():
        logger.error('Unexpected error: ' + sys.exc_info()[0])
        sys.exit(0)