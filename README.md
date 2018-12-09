# Exercise Database
A simple user generated exercise website. The website allows users to navigate between various body parts and explore exercises that have been provided by the user community. Feel free to add any of your own content.

The site uses a sqlite database along with python and flask to render HTML webpages.

Feel free to visit the site at http://www.13.127.13.230.xip.io


## Prerequisites

* ### Python
The program runs on Python 2.
Download Python 2 [here](https://www.python.org/downloads/).

* ### VirtualBox
A Virtual Machine hosting service. Download VirtualBox [here](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1).

* ### Vagrant
The software used to configure your virtual machine allowing you to share files between your host computer and the virtual machine, works with VirtualBox. Download Vagrant [here](https://www.vagrantup.com/downloads.html).

* ### Database Setup
The database is already set up however if you would like to start with a fresh database, run the ```database_setup.py``` file by executing ```python database_setup.py``` from your terminal. A database entitled ```exercises.db``` will be created.

## Instructions
* Run the ```main.py``` file via Python by using the following command ```python2.7 main.py```. The server is configured to run on port ```8000```. Visit http://localhost:8000 and the site should appear.
* The application can be run from either your main terminal or via your vagrant machine.

## Notes
* If you would like to change the port that the file is run on, change line ```502``` ```port=8000``` to your desired port.

## Python Version

Program is run using Python 2.7.12

# Connection Information

### IP Address
* 13.127.13.230

### SSH Port
* 2200
