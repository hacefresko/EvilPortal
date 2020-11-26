#!/bin/bash

tempFolder="/tmp/evilportal"

num=$(grep "<wireless-network"  $tempFolder/temporal-01.kismet.netxml | wc -l)
begLines=$(grep -n "<wireless-network" $tempFolder/temporal-01.kismet.netxml | cut -d ":" -f 1)
endLines=$(grep -n "</wireless-network>" $tempFolder/temporal-01.kismet.netxml | cut -d ":" -f 1)

i=1
apNum=1
while [ $i -le $num ]
do
	beg=$(echo $begLines | cut -d " " -f $i)
	end=$(echo $endLines | cut -d " " -f $i)
	isProbe=$(grep "<wireless-network" $tempFolder/temporal-01.kismet.netxml | cut -d "=" -f 3 | cut -d "\"" -f 2 | sed -n "$i"p)

	if [ "$isProbe" == "probe" ]
	then
		tClientBSSID[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep BSSID -m 1 | cut -d ">" -f 2 | cut -d "<" -f 1)
		tManufacturer[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep manuf -m 1 | cut -d ">" -f 2 | cut -d "<" -f 1 )
		tSSID[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep ssid | cut -d ">" -f 2 | cut -d "<" -f 1)
		tchannel[$apNum]=$(sed -n "$beg","$end"p $tempFolder/temporal-01.kismet.netxml | grep channel -m 1 | cut -d ">" -f 2 | cut -d "<" -f 1)

		if [ -z "${tSSID[$apNum]}" ]
		then
			tSSID[$apNum]="Unknown"
		fi

		if [ -z "${tManufacturer[$apNum]}" ]
		then
			tManufacturer[$apNum]="Unknown"
		fi

		apNum=$(( $apNum + 1 ))
	fi
	i=$(( $i + 1 ))
done

echo "PROBE REQUESTS"
echo "Network interface: $interface"
echo "+----+----------------------------------+-------------------+-------+--------------------------------------+"
echo "|  i |             AP SSID              |    CLIENT MAC     |CHANNEL|         CLIENT MANUFACTURER          |"
echo "+----+----------------------------------+-------------------+-------+--------------------------------------+"
i=1
while [ $i -lt $apNum ]
do
	printf  '%1s %2s %1s %-32.32s %1s %17s %1s %3s %3s %-36.36s %1s\n'  "|" "$i" "|" "${tSSID[$i]}" "|" "${tClientBSSID[$i]}" "|" "${tchannel[$i]}" "|" "${tManufacturer[$i]}" "|"
	i=$(( $i + 1 ))
done
echo "+----+----------------------------------+-------------------+-------+--------------------------------------+"
echo
