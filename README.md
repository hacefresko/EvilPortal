# EvilPortal

EvilPortal is a script to perform phishing attacks through captive portals.

It can perform various techniques, such as Evil Twin or Karma, to prompt captive portals
among users who connect to the access point.

It has been tested in Kali (run.sh) and Raspbian (raspberry_run.sh)

## Programs used: 
- airmon-ng
- dnsmasq
- hostapd
- macchanger
- apache2
- php7.3
- mariaDB (mysql)
- gnome-terminal (desktop version)
- screen (raspberry version)

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

- **Option 1**: Create new access point (1 network interface with monitor mode needed)

1. Creates new access point with hostapd

2. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface 

3. When a device connects to the acces point, it check for the quality of the conenction
   by sending a GET request to some of the default pages such as 
   connectivitycheck.gstatic.com/generate_204 and gets redirected to the captive portal *
		   

- **Option 2**: (Evil Twin) Intercept existing access point (2 network interface with monitor mode needed)

1. Selects existing access point
		
2. Creates new access point with the same parameters as the existing one with hostapd (some must be provided by the user)
		
3. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface
		
4. Takes down the original access point with aireplay so the victim connects to us thinking
   it's connecting back to the original
	
5. When a device connects to the acces point, it check for the quality of the conenction
   by sending a GET request to some of the default pages such as 
   connectivitycheck.gstatic.com/generate_204 and gets redirected to the captive portal *


- **Option 3**: (Karma) Create access point recogniced by the victim (1 network interface with monitor mode needed)

1. Sniffs probe requests containing the ESSID of the access points which free devices have recently been
   conneceted and are willing to connect now

2. Creates new access point with the ESSID contained in the selected probe request (encryption must be provided by the user)

3. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface

4. When a device connects to the acces point, it check for the quality of the conenction
   by sending a GET request to some of the default pages such as 
   connectivitycheck.gstatic.com/generate_204 and gets redirected to the captive portal *

  

### * Comment  
 -If the attacker has Internet connection:
  Iptables redirects the requests to the Apache server which sends a 302 response pointing 
  to our fake captive portal login page (mod_rewrite). Every device is affected.  
 
 -If the attacker doesn't have Internet connection: 
  Dnsmasq redirects every request to the Apache server which sends a 302 response pointing
  to our fake captive portal login page (mod_rewrite). With this method, Samsung devices are
  not affected as they use a different captive portal detection system, involving Internet 
  connection.
  
  
# Disclaimer
This tool was made for learning purposes and security testing of my own networks.
Please, do not use without the consent of the WiFi/devices owners or any other illegal
activities.
  

