import os, re

def title():
    print()
    print('███████╗██╗   ██╗██╗██╗     ██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗     ')
    print('██╔════╝██║   ██║██║██║     ██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║     ')
    print('█████╗  ██║   ██║██║██║     ██████╔╝██║   ██║██████╔╝   ██║   ███████║██║     ')
    print('██╔══╝  ╚██╗ ██╔╝██║██║     ██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║     ')
    print('███████╗ ╚████╔╝ ██║███████╗██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗')
    print('╚══════╝  ╚═══╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝')
    print('                                                       By: hacefresko         ')
    print()


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

    def printInterfaces(self):
        ret = ''

        for interface in self.interfaces:
            if interface['mode'] == 'monitor':
                ret += '[{}] -> {} ({})'.format(interface['i'], interface['name'], interface['mode'])
            else:
                ret += '[{}] -> {}'.format(interface['i'], interface['name'])

        return ret

    def putInMonitor(self, i):
        if type(i) is not int:
            print('[x] Input value is not an integer!')
            return -1

        if i < 0 or i >= self.num:
            print('[x] Input value out of bounds!')
            return -1

        interface = self.interfaces[i]

        if interface['mode'] == 'monitor':
            print('[x] Selected interface is already in monitor mode!')
            return -1
        
        os.system('ifconfig ' + interface['name'] + ' down')
        os.system('iw ' + interface['name'] + ' set type monitor')
        os.system('ifconfig ' + interface['name'] + ' up')

        f = open(self.netIntDir + '/' + interface['name'] + '/type', 'r')
        if f.read() != '803\n':
            print('[x] Newtork interface couldn\'t be put in monitor mode!')
            f.close()
            return -1
        f.close()
        
        return 0

