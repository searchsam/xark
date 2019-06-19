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
        self.c.close()
        self.conn.close()

    def set(self, query, data):
        self.c.executemany(query, data)
        self.conn.commit()
        self.c.close()
        self.conn.close()


class Xark():

    def __init__(self):
        self.db = Conexion()
        # Fecha actual en entero
        day = int(datetime.datetime.now().strftime('%Y%m%d'))
        # Estado de sincronizacion en `No Sincronizado`
        # self.sync_status = False

        #Consulta si existe el registro de hoy
        query = self.db.get(
            'SELECT sync_status, collect_status FROM xark_status WHERE create_at=?',
            [(day)]
        )
        print(query)

        try:
            self.sync_status = query[0]
            # Estado de recoleccion en `No Recolectado`
            self.collec_status = query[1]
        except ():
            self.sync_status = False
            # Estado de recoleccion en `No Recolectado`
            self.collec_status = False

            #Si el registro no existe, lo crea.
            self.db.set("INSERT INTO xark_status(create_at, sync_status, collect_status, sync_date, collect_date)VALUES(?,?,?,?,?)",
                        [(day, False, False, datetime.datetime.now(), datetime.datetime.now())])

        # self.collec_status = False
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

        try:
            self.db.set(
                'INSERT INTO data_xo(serial, uuid, create_at, update_at)VALUES(?,?,?,?)',
                [
                    (
                        data['serialnum'],
                        data['uuid'],
                        datetime.datetime.now(),
                        datetime.datetime.now(),
                    )
                ],
            )
        except sqlite3.IntegrityError as e:
            print(e)

        return data

    def collection(self):
        '''Funcion para recolectar informacion'''
        data = None
        if not self.collec_status:
            print("entrando")
            # Termina la funcion ya se ha recolectado informacion
            data = self.getSerialNumber()
            # Estado de sincronizacion en `Sincronizado`
            self.collec_status = True
            return self.collec_status

        return data

    def synchrome(self, data):
        '''Funcion para sincronizar con el charco.'''
        if self.sync_status:
            # Termina la funcion si ya se a sincronizacion con el charco
            return self.sync_status
        # Verifica si el IIAB esta disponible
        print('Verificacion a : {}'.format(datetime.datetime.now()))
        code = subprocess.Popen(
            'curl -o /dev/null -s -w "%{http_code}\n" http://10.0.11.33:5000/',
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.readlines()
        code = int(code[0].strip())

        if code == 200:
            url = 'http://10.0.11.33:5000/data/{0}/{1}'.format(
                data['serialnum'], data['uuid']
            )
            result = subprocess.Popen(
                'curl -o /dev/null -s -w "%{http_code}\n" ' + url,
                shell=True,
                stdout=subprocess.PIPE,
            ).stdout.readlines()

            print(result[0].strip())
            result = int(result[0].strip())
            if code == 200:
                # Estado de sincronizacion en `Sincronizado`
                self.sync_status = True
                return self.sync_status
            else:
                self.s.enter(3600, 1, self.synchrome, ())
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
                processes.append(multiprocessing.Process(target=xark.collection, args=()))
                # Sincronizar con el charco
                processes.append(multiprocessing.Process(target=xark.synchrome, args=()))
                # Inicia los procesos.
                for process in processes:
                    process.start()
                for process in processes:
                    process.join()
        else:
            exit('Fin de la ejecucion')
    except Exception():
        logger.error('Unexpected error: ' + sys.exc_info()[0])
        sys.exit(0)
