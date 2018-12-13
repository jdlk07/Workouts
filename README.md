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
The database is already set up however if you would like to start with a fresh database, run the ```database_setup.py``` file by executing ```python database_setup.py``` from your terminal. A database entitled ```exercises.db``` will be created. This creates an SQLite database.

* ### Apache2 Web Server
The application runs on an Apache2 Web Server. To install the web server on your linux machine, use the following commands to first update the local package index and then install Apache.
```
 sudo apt-get update

 sudo apt-get install apache2
```


## Instructions
* Run the ```main.py``` file via Python by using the following command ```python2.7 main.py``` to run the app locally. It can be accessed at http://localhost:8000 when run directly from the ```main.py``` file locally.

* If running the app through a server via Apache2, please see the following [instructions](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps) for how to set up a Flask application to run on an apache2 server.


## Python Version

Program is run using Python 2.7.12

# Connection Information

IP Address ```13.127.13.230```

SSH Port ```2200```

## Notes / Resources / Useful Links
* If you would like to change the port that the file is run on when running locally directly from the ```main.py``` file, change line ```502``` ```port=8000``` to your desired port.
* [SSH connection issues](https://www.digitalocean.com/community/tutorials/ssh-essentials-working-with-ssh-servers-clients-and-keys)
* [Understanding SSH Keypairs](https://winscp.net/eng/docs/ssh_keys)
* [How to deploy a Fask Application on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)
* [Amazon Web Services for hosting a server](https://aws.amazon.com/)
* [How to install Apache Web Server on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-the-apache-web-server-on-ubuntu-16-04)
* [XIP.IO for converting an IP address to a suitable domain name](http://xip.io/)
