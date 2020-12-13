# EvilPortal

EvilPortal is a python script to perform phishing attacks through captive portals.

It can perform various techniques, such as Evil Twin or Karma, to prompt captive portals among users who connect 
to the access point.

It has been tested in Kali (run.py) and Raspbian (raspberry_run.py).

Recall that this script depends much on the interface used, the devices' protocols, the access
points and devices itself or even on the country, so it may not work on every device out there (ie. routers with Protected Management Frames are not vulnerable to Evil Twin, as they are protected against deauth attacks).

## Requirements
- scapy (Python3)
- dnsmasq
- hostapd
- apache2
- php (you can select your version in the 3rd line of the script)
- mariaDB (mysql)

## Before running the script:
- Put the fake captive portal in directory /captive, with a similar user/password structure as the example 
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

## How does it work:

All 4 modes use different techniques to create a WiFi access point which the victims will connect to.

When a device connects to the acces point, it checks for the quality of the conenction by sending a GET
request to some of the default pages, such as connectivitycheck.gstatic.com/generate_204 or www.msftncsi.com. 
When the device queries the DNS server (dnsmasq), it responds with the address of the Apache server. 
The .htaccess file makes the server send a 302 response redirecting the device to the actual captive portal (/captive). 
This 302 is what indicates the device that this is a captive portal.

Where the different modes differ, is in the way they get the victims to connect to the access point:

- **Mode 1**: Create new access point (1 network interface with monitor mode needed)

	1. Creates a new access point with hostapd given some information provided by the user (SSID, encryption and channel)

	2. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the network interface 

	3. Victims connect to our ap
		   

- **Mode 2**: (Evil Twin) Intercept existing access point (2 network interface with monitor mode needed)

	1. Sniffs beacon frames to get SSIDs, channels and BSSIDs from nearby access points

	2. With the information gathered, it selects an access point and creates an identical one (encryption must 
	   be provided by user)

	3. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface

	4. Takes down the original access point by sending deauth frames, so the clients connects to us thinking
	   they're connecting back to the original ap


- **Mode 3**: (Evil Twin) Intercept clients connected to access point (2 network interface with monitor mode needed)

	1. Sniffs beacon and data frames to get SSIDs, channels and BSSIDs from nearby access points, showing only
	   the ones with clients connected to them (and also showing the MAC address of the clients).

	2. With the information gathered, it selects an access point and creates an identical one (again, encryption
	   must be provided by user)

	3. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface

	4. Takes down the original access point by sending deauth frames, so the clients connects to us thinking
	   they're connecting back to the original ap
   

- **Mode 4**: (Karma Attack) Create access point recogniced by the victim (1 network interface with monitor mode needed)

	1. Sniffs probe requests to get ESSIDs of the access points which free devices have recently been conneceted and are 
	   willing to connect to now

	2. Creates new access point with the ESSID contained in the selected probe request (encryption must be provided by the user)

	3. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface

	4. Victims connect to our ap
  
  
# Disclaimer
This tool was made for learning purposes and security testing of my own networks.
Please, do not use without the consent of the WiFi networks/devices owners or any other illegal activities.
User discrection is advised.
  

