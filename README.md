# Captive phishing

Bash script for creating a WiFi access point or intercepting and existing one and perform
phishing via a captive portal

Programs needed: 
- dnsmasq
- hostapd
- macchanger
- apache2
- gnome-terminal

Usage:
- Put the fake captive portal  in directory /captive, with a similar user/password
  structure as the example provided in index.html
- Change wifi name
- Create the following database:

```
service mysql start
mysql
MariaDB [(none)]> create database fakeap;
MariaDB [(none)]> create user user;
MariaDB [(none)]> grant all on fakeap.* to 'user'@'localhost' identified by 'password';
MariaDB [(none)]> use fakeap
MariaDB [fakeap]> create table accounts(email varchar(30), password varchar(30));
MariaDB [fakeap]> ALTER DATABASE fakeap CHARACTER SET 'utf8';
MariaDB [fakeap]> select * from accounts;
```

How does it work:

	[1] Create new WiFi

	1.  Creates the WiFi access point.
	
	2.  Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface 

	3.  When a device connects to the acces point, it check for the quality of the conenction
	    by sending a GET request to some of the default pages such as connectivitycheck.gstatic.com/generate_204

	3.1 If the attacker has Internet connection:
	    Iptables redirects the requests to the Apache server which sends a 302 response pointing 
	    to our fake captive portal login page (mod_rewrite). Every device is affected.

	3.2 If the attacker has no Internet connection: 
	    Dnsmasq redirects every request to the Apache server which sends a 302 response pointing
	    to our fake captive portal login page (mod_rewrite). With this method, Samsung devices are
	    not affected as they use a different captive portal detection system, involving Internet 
	    connection (I am still investigating why).
