# Captive phishing

Bash script to create a WiFi access point or intercept an existing one and perform phishing 
through a captive portal. 

Programs needed: 
- airmon-ng
- dnsmasq
- hostapd
- macchanger
- apache2
- gnome-terminal

Before running the script:
- Put the fake captive portal in directory /captive, with a similar user/password structure as the example 
  provided in index.html and add the names of the files to the .htaccess file with the correct format
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

	[1] Create new access point (1 network interface with monitor mode needed)

		1. Creates new access point with hostapd

		2. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface 

		3. When a device connects to the acces point, it check for the quality of the conenction
		   by sending a GET request to some of the default pages such as 
		   connectivitycheck.gstatic.com/generate_204 and gets redirected to the captive portal *
		   
		   
	[2] Intercept existing access point (2 network interface with monitor mode needed)

		1. Select existing access point
		
		2. Creates new access point with the same parameters as the existing one with hostapd
		
		3. Creates a DHCP and a DNS server with dnsmasq which assign a domain name to the wifi interface
		
		4. Takes down the original access point with aireplay
		
		5. When a device connects to the acces point, it check for the quality of the conenction
		   by sending a GET request to some of the default pages such as 
		   connectivitycheck.gstatic.com/generate_204 and gets redirected to the captive portal *


		* If the attacker has Internet connection:
		  Iptables redirects the requests to the Apache server which sends a 302 response pointing 
		  to our fake captive portal login page (mod_rewrite). Every device is affected.
		  If the attacker has no Internet connection: 
		  Dnsmasq redirects every request to the Apache server which sends a 302 response pointing
		  to our fake captive portal login page (mod_rewrite). With this method, Samsung devices are
		  not affected as they use a different captive portal detection system, involving Internet 
		  connection (I am still investigating why).
