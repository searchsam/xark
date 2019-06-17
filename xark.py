#!/usr/bin/python

'''
XO Agil Recolector Kaibil - XARK

Recolector de informacion interno de la XO. Actualmentle solo recolecta:
    * Serial number
'''

import sys
import requests


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
    r = requests.get('http://10.0.11.33:5000/')
    if r.status_code == 200:
        n = requests.get('http://10.0.11.33:5000/data/{0}/{1}'.format(data['serialnum'], data['uuid']))
        print(n.url)
        print(n.text)
