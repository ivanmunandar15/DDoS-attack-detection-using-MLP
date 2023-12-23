from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import OVSKernelSwitch, RemoteController
from time import sleep
from datetime import datetime
from random import randrange, choice

class MyTopo(Topo):
    def build(self):
        switches = []
        hosts = []

        for s in range(1, 6):
            switch_name = 's{}'.format(s)
            switch = self.addSwitch(switch_name, cls=OVSKernelSwitch, protocols='OpenFlow13')
            switches.append(switch)

            for h in range(1, 4):
                host_name = 'h{}'.format(s * 3 + h - 3)
                host_ip = '10.0.0.{}/24'.format(s * 3 + h - 3)
                host = self.addHost(host_name, cpu=1.0/20, mac="00:00:00:00:00:{:02d}".format(s * 3 + h - 3), ip=host_ip)
                hosts.append(host)
                self.addLink(host, switch)

        for i in range(len(switches) - 1):
            self.addLink(switches[i], switches[i + 1])

def ip_generator():
    return "10.0.0.{}".format(randrange(1, 16))

def startNetwork():
    topo = MyTopo()
    c0 = RemoteController('c0', ip='127.0.0.1')
    net = Mininet(topo=topo, link=TCLink, controller=c0)
    net.start()

    h1 = net.get('h1')
    hosts = [net.get(f'h{i}') for i in range(1, 16)]

    h1.cmd('cd /home/mininet/webserver')
    h1.cmd('python3 -m http.server 80 &')
    
    for attack_type in ['ICMP (Ping) Flood', 'UDP Flood', 'TCP-SYN Flood', 'DNS Amplification']:
        src = choice(hosts)
        dst = ip_generator()
        print("--------------------------------------------------------------------------------")
        print(f"Performing {attack_type}")
        print("--------------------------------------------------------------------------------")
        if attack_type == 'DNS Amplification':
            src.cmd(f"timeout 20s hping3 --rand-source -p 53 --flood --data 100 {dst}")
        else:
            protocol_flag = '-1' if attack_type == 'ICMP (Ping) Flood' else '-2' if attack_type == 'UDP Flood' else '-S' if attack_type == 'TCP-SYN Flood' else ''
            src.cmd(f"timeout 20s hping3 {protocol_flag} -V -d 120 -w 64 -p 80 --rand-source --flood {dst}")
        sleep(100)

    print("--------------------------------------------------------------------------------")
    net.stop()

if __name__ == '__main__':
    start = datetime.now()
    setLogLevel('info')
    startNetwork()
    end = datetime.now()
    print(f"Total time: {end - start}")