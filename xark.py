#!/usr/bin/python

'''
XO Agil Recolector Kaibil - XARK

Recolector de informacion interno de la XO. Actualmentle solo recolecta:
    * Serial number
'''

import sys
import subprocess


def getSerialNumber():
    data = dict()
    f = open('/home/.devkey.html', 'r')
    for value in f:
        if 'serialnum' in value or 'uuid' in value:
            value = value.strip().split(' ')
            data[value[2].split('=')[1].replace('"', '')] = value[3].split('=')[1].replace('"', '')
    return data


if __name__ == '__main__':
    data = getSerialNumber()
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
