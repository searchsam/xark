# XARK

Baby SAHRK hunting for device information without supervision.

## Data

Data extracted from the OX laptop.

- Número de serie (Serial Number)
- UUID (Universally Unique IDentifier)
- Actividades Instaladas (Installed activities)
- Diaro (Journal Activity)
- Registros de Actividades (Activities logs)
- RAM
- ROM
- Procesador (Processor)
- Arquitectura (Architecture)
- Georeference
- MAC

## Información del Dispositivo

### Número de Serie

El número de serie es el identificador de la laptop XO dentro de Fundación Zamora Téran. En una cadena de 11 caracteres formado por las letras de la `A-Z` y números del `0-9`.

El Número de Serie se encuentra en el directorio `/home/.devkey`:

```html
<input type="hidden" name="serialnum" value="CQF4460082A" />
```

### UUID

El UUID o Identificador Unico Universal es un identificador de hardware unico por laptop. Es una cadena de 36 caracteres de la A-Z y 0-9 incluyendo '-'.

Esta secuencia de caracteres esta contituida por 5 secciones:

1. Primera sección: Compuesta por 8 caracteres `CADA4D11`.
2. Segunda sección: Compuesta por 4 caracteres `F284`.
3. Tercera sección: Compuesta por 4 caracteres `BAFC`.
4. Cuarta sección: Compuesta por 4 caracteres `DACE`.
5. Quinta sección: Compuesta por 12 caracteres `B97DCD2DFFBB`.

Dando un total de 32 caracteres más 4 guiones `-` que separan cada sección dando un total de 36 caracteres en total.

El UUID se encuentra en el directorio `/home/.devkey`:

```html
<input type="hidden" name="uuid" value="CADA4D11-F284-BAFC-DACE-B97DCD2DFFBB" />
```

### Actividades Instaladas

Cada Actividad instalda en el sistema genera un directorio en `~/Activities` o `Actividades` con el nombre de la actividad a como se genera en el archivo `activity` del Diario.

### Diario

El Diaro es una Actividad de la OLPC XO Laptop encargada de llegar registro de toda las acciones en al Laptop. La Actividad Diaro guarda registro de cada actividad instalada y usada en el directorio `~/.sugar/defauld/datastore`.

En este directorio se genera toda la metadata en un directorio por cada Actividad. Estas carpetas se nombran con los dos primeros caracteres del UID (Identificador Unico) respectivo a cada Actividad `56`. Dentro de esta carpeta se encuestra otra carpeta nombrada con el UID (Identificador Unico) completo `56c315c3-13f1-483e-8846-a57d443f6e0b` (El UID-Identificador Unico tiene el mismo formato que el UUID-Identificador Universal Unico) y a su ves hay dentro otra carpeta llamada `metadata` quedando un arbol de directorio de la siguiente manera `~/.sugar/defauld/datastore/56/56c315c3-13f1-483e-8846-a57d443f6e0b/metadata`.

El registro de la cada actividad se guadar en 17 archivos que son modificados en relación a que dicha Actividad este en siendo usada. Estos archivos son:

- `activity`: Nombre del directorio en la actividad guarda sus recursos `org.laptop.Terminal`.
- `activity_id`: Identificador en la actividad en el sistema `514fd934b0d86f428d41b1563cea956c66dc522f`.
- `checksum`: Veriicador de cambios `8b156ed600d1dac3a088e06f250f62ea`.
- `creation_time`: Fecha en timestamp de la creacion de la metadata `1561158783`.
- `filesize`: Tamaño de la metadata `2622`.
- `icon-color`: Color del icono de la Actividad `#00A0FF,#00588C`. El color del icono cambia luego de ser usada por primera vez.
- `keep`: Identificador de persistencia de archivos `0`.
- `launch-times`: Hora en timestamp de las veces que se ha ejecutado la Actividad `1561158124, 1561161311, 1561167124, 1561168059`.
- `mime_type`: Tipo de la data que genera o usa la Actividad `text/plain`.
- `mountpoint`: El punto de montaje que usa la Actividad para ser ejecutada `/`.
- `mtime`: `2019-06-21T20:31:41.274168`.
- `share-scope`: `private`.
- `spent-times`: Tiempo en segundos de consumo de recursos del sistema `1360, 32, 414, 2616`.
- `timestamp`: Tiempo de segundos de la ultima ejecucion `1561170701`.
- `title`: Nombre que el sistema muestra `Actividad Terminal`.
- `title_set_by_user`: Nombre establecido por el usuario para ser mostrado en el sistema `0`.
- `uid`: Identificador Unico `56c315c3-13f1-483e-8846-a57d443f6e0b`.
- `preview`: Miniatura que se muestra en el sistema `imagen`. Para efecto de xark no sera tomado en cuanta.

### RAM

Memoria RAM en bytes.

```bash
$ free -m
              total        used        free      shared  buff/cache   available
Mem:           7857        6089         400         418        1367         965
Swap:          7987         112        7875
```

## Recursos

- <http://wiki.laptop.org/go/Activation_and_Developer_Keys#Getting_a_developer_key>
- <http://wiki.laptop.org/go/Journal_Activity>
- <http://wiki.laptop.org/go/School_server>
- <http://wiki.laptop.org/go/School_Identity_Manager>
- <https://stackoverflow.com/questions/17304225/how-to-detect-if-computer-is-contacted-to-the-internet-with-python>
- <https://www.raspberrypi.org/forums/viewtopic.php?t=173157>
