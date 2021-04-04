# EvilPortal

![Banner](https://raw.githubusercontent.com/hacefresko/EvilPortal/master/git%20resources/banner.png)

EvilPortal is a python script to perform phishing attacks through captive portals.

It can perform various techniques, such as Evil Twin or Karma, to prompt captive portals among users who connect 
to the access point.

It has been tested in Kali, Ubuntu and Raspbian

Recall that this script depends much on the interface used, the devices' protocols, the access points and devices 
itself or even on the country, so it may not work on every device out there (ie. routers with Protected Management Frames 
are not vulnerable to Evil Twin, as they are protected against deauth attacks).


## Requirements
- Python3
- scapy
- dnsmasq
- hostapd
- apache2
- php (version can be specified at the beginning of the script)
- php-mysqli
- mysql


## Usage:
- Put your fake captive portal in directory /captive, with a similar user/password structure as the example 
  provided in index.html
- Create the following database:

```
$ service mysql start
$ mysql
MariaDB [(none)]> create database fakeap;
MariaDB [(none)]> create user user;
MariaDB [(none)]> grant all on fakeap.* to 'user'@'localhost' identified by 'password';
MariaDB [(none)]> use fakeap
MariaDB [fakeap]> create table accounts(email varchar(30), password varchar(30));
MariaDB [fakeap]> alter database fakeap character set 'utf8';
MariaDB [fakeap]> select * from accounts;
```

- In Ubuntu/Debian
```
$sudo python3 run.py
```

- In Raspbian
```
$sudo python3 raspberry_run.py
```


## How does it work:

- **Rogue AP**: Creates new AP with the data provided by the user. Requires 1 interface with monitor mode.

- **Evil Twin**: Sniffs beacon frames to find available APs. Then, selected one is taken down with deauth packets and 
clients who were connected to it now connect to us. Alternatively, it can also sniff data packets to show only APs with
connected clients. Requires 2 network interfaces with monitor mode.

- **Karma**: Sniffs probe requests to find APs that clients are willing to connect to. Requires 1 interface with monitor 
mode.

- **Known Beacons**: Sends beacon frames with known SSIDs from open WiFis. Then, it sniffs probe requests to check if any 
device recognices the AP and wants to connect to it so it creates it. Requires 1 interface with monitor mode.

For all mentioned modes, once we have the required data, hostapd creates the access point according to it.

Then, dnsmasq creates the DHCP and the DNS servers and the Apache web server and the SQL database are configured.

Now, access point is ready. When a device connects, it checks for the quality of the connection by sending a GET
request to some of the default pages, such as connectivitycheck.gstatic.com/generate_204 or www.msftncsi.com. 
When the device queries the DNS server (dnsmasq), it responds with the address of the Apache server. 
Then, the .htaccess file makes the server send a 302 response redirecting the device to the actual captive portal (/captive). 
This 302 redirection is what indicates to the device that this is a captive portal.
  
  
## Disclaimer
This tool was made for learning purposes and security testing of my own networks.
Usage of this tool against infrastructures without the consent of the owner can be considered as an illegal activity.
Authors assume no liability and are not responsible for any misuse or damage caused by this program.
