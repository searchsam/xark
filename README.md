# XARK

Baby SAHRK hunting for device information without supervision.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

Xark requires that you have python installed.

```bash
# Fedora 22 and higher
$ sudo dnf install python

# Fedora 21 and older
$ sudo yum install python
```

### Installing

Clone the repo

```bash
$ git clone https://github.com/searchsam/xark.git
```

or download the latest version of the [releases page](https://github.com/searchsam/xark/releases) and unzip it.

Go into the project folder and create a new `.env` file from `env.example` and filled with your environtment data.

```bash
$ mv env.example .env
```

once your `.env` file has the data of your environment run the `setup.sh` file

```bash
sh setup.sh
```

The `setup.sh` file among other things will create the file `xarkd.service`. The `xarkd.service` is a Systemd's Unit Service, copy this file to `/etc/systemd/system` to run Xark as a systemd service or at start system.

```bash
sudo cp xarkd.service /etc/systemd/system/. # Copy xarkd.serve to Unit Service
sudo systemctl start xarkd.service # Init Xark as Systemd Service
sudo systemctl enable xarkd.service # Init Xark at start system
```

Or just start Xark directly from the project folder wit python

```bash
python xark.py
```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/searchsam/xark/tags).

## Authors

- **Samuel Gutiérrez** - _Initial work_ - [searchsam](https://github.com/searchsam)

See also the list of [contributors](https://github.com/searchsam/xark/graphs/contributors) who participated in this project.

## License

This project is licensed under the Apache License - see the [LICENSE.md](./LICENSE.md)

## Acknowledgments

- <http://wiki.laptop.org/go/Activation_and_Developer_Keys#Getting_a_developer_key>
- <http://wiki.laptop.org/go/Journal_Activity>
- <http://wiki.laptop.org/go/School_server>
- <http://wiki.laptop.org/go/School_Identity_Manager>
- <https://stackoverflow.com/questions/17304225/how-to-detect-if-computer-is-contacted-to-the-internet-with-python>
- <https://www.raspberrypi.org/forums/viewtopic.php?t=173157>
