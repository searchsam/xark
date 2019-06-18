#!/usr/bin/python

'''
XO Agil Recolector Kaibil - XARK

Recolector de informacion interno de la XO. Actualmentle solo recolecta:
    * Serial number
    * UUID
'''

import sys
import logging
import datetime
import subprocess

# Logging setting
logger = logging.getLogger('xark')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-s - %(message)s')
handler = logging.FileHandler(filename='/var/log/xark.log', mode='a')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Xark():

    def __init__(self):
        self.date = datetime.date.today()
        self.init = 0

    def getSerialNumber(self):
        '''Capturar Numero de serie y UUID'''
        data = dict()
        f = open('/home/.devkey.html', 'r')
        for value in f:
            if 'serialnum' in value or 'uuid' in value:
                value = value.strip().split(' ')
                data[value[2].split('=')[1].replace('"', '')] = value[3].split('=')[1].replace('"', '')
        return data

    def collection(self):
        '''Recolectar informacion'''
        self.getSerialNumber()

    def synchrome(self, data):
        '''Funcion principal. Copia un archivo arhivo de una determinada marca
        y caracterisca a su respectiva tabla, si el copy no es exitoso
        guarda el nombre del archivo en un archivo JSON.

        Args:
            COLUMNS (list): Lista de columnas de la tabla.
        '''
        code = subprocess.Popen(
            'curl -o /dev/null -s -w "%{http_code}\n" http://10.0.11.33:5000/',
            shell=True,
            stdout=subprocess.PIPE
        ).stdout.readlines()
        code = int(code[0].strip())
        if code == 200:
            url = 'http://10.0.11.33:5000/data/{0}/{1}'.format(data['serialnum'], data['uuid'])
            result = subprocess.Popen(
                'curl -o /dev/null -s -w "%{http_code}\n" ' + url,
                shell=True,
                stdout=subprocess.PIPE
            ).stdout.readlines()
            print(result[0].strip())


if __name__ == '__main__':
    try:
        # Log de inicio diario
        logger.info('Inicio de dia {}'.format(datetime.datetime.now()))
        # Instancia del Kaibil
        xark = Xark()
        # Ciclo infinito
        while True:
            # Verifica si el dia de la semana es entre lunes y viernes
            if datetime.datetime.now().weekday() > 1 and datetime.datetime.now().weekday() < 5:
                # Verifica que la hora del dia sea entre las 6:00 y las 18:00
                if datetime.datetime.now().time() > datetime.time(6, 0) and datetime.datetime.now().time() < datetime.time(18, 0):
                    # Recolectar informacion
                    xark.collection()
                    xark.synchrome()
            else:
                exit(1)
    except() as e:
        logger.error('{}'.format(e))
        sys.exit(0)
