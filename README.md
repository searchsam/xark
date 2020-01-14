# Initial page



```text
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
- Kernel (kernel)
- Arquitectura (Architecture)
- MAC
- Georeference

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

### ROM

```bash
$ df -H
S.ficheros              Tamaño Usados  Disp Uso% Montado en
devtmpfs                  4.2G      0  4.2G   0% /dev
tmpfs                     4.2G   188M  4.0G   5% /dev/shm
tmpfs                     4.2G   1.6M  4.2G   1% /run
tmpfs                     4.2G      0  4.2G   0% /sys/fs/cgroup
/dev/mapper/fedora-root    53G    19G   32G  37% /
tmpfs                     4.2G   1.3M  4.2G   1% /tmp
/dev/sda2                 1.1G   205M  748M  22% /boot
/dev/mapper/fedora-home   173G   152G   13G  93% /home
/dev/sda1                 210M    19M  191M   9% /boot/efi
tmpfs                     824M    58k  824M   1% /run/user/1000
```

### Kernel

```bash
$ uname -a
Linux localhost.localdomain 5.1.11-300.fc30.x86_64 #1 SMP Mon Jun 17 19:33:15 UTC 2019 x86_64 x86_64 x86_64 GNU/Linux
```

### Arquitectura

```bash
$ lscpu
Arquitectura:                        x86_64 # tomado
modo(s) de operación de las CPUs:    32-bit, 64-bit
Orden de los bytes:                  Little Endian
Tamaños de las direcciones:          39 bits physical, 48 bits virtual
CPU(s):                              4 # tomado
Lista de la(s) CPU(s) en línea:      0-3
Hilo(s) de procesamiento por núcleo: 2
Núcleo(s) por «socket»:              2
«Socket(s)»                          1
Modo(s) NUMA:                        1
ID de fabricante:                    GenuineIntel
Familia de CPU:                      6
Modelo:                              142
Nombre del modelo:                   Intel(R) Core(TM) i5-7200U CPU @ 2.50GHz # tomado
Revisión:                            9
CPU MHz:                             823.721
CPU MHz máx.:                        3100.0000
CPU MHz mín.:                        400.0000
BogoMIPS:                            5424.00
Virtualización:                      VT-x
Caché L1d:                           32K
Caché L1i:                           32K
Caché L2:                            256K
Caché L3:                            3072K
CPU(s) del nodo NUMA 0:              0-3
Indicadores:                         fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp md_clear flush_l1d
```

### MAC

```bash
$ cat /sys/class/net/$IFACE/address
e4:70:b8:cf:51:f7
```

## Recursos

- <http://wiki.laptop.org/go/Activation_and_Developer_Keys#Getting_a_developer_key>
- <http://wiki.laptop.org/go/Journal_Activity>
- <http://wiki.laptop.org/go/School_server>
- <http://wiki.laptop.org/go/School_Identity_Manager>
- <https://stackoverflow.com/questions/17304225/how-to-detect-if-computer-is-contacted-to-the-internet-with-python>
- <https://www.raspberrypi.org/forums/viewtopic.php?t=173157>
```

