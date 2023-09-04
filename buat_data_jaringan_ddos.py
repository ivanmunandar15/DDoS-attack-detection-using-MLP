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
        # Definisi topologi seperti sebelumnya
        
        s = []

        # Add switches
        for i in range(1, 6):
            switch = self.addSwitch(f's{i}', cls=OVSKernelSwitch, protocols='OpenFlow13')
            s.append(switch)

        # Add hosts
        hosts = []
        for i in range(1, 16):
            host = self.addHost(f'h{i}', cpu=1.0/20, mac=f"00:00:00:00:00:{i:02}", ip=f"10.0.0.{i}/24")
            hosts.append(host)

        # Add links
        for i in range(0, 15):
            self.addLink(hosts[i], s[i // 3])

        for i in range(0, 4):
            self.addLink(s[i], s[i + 1])

def ip_generator():
    ip = ".".join(["10", "0", "0", str(randrange(1, 16))])
    return ip

def startNetwork():
    topo = MyTopo()
    c0 = RemoteController('c0', ip='192.168.0.101', port=6653)
    net = Mininet(topo=topo, link=TCLink, controller=c0)
    net.start()

    h1 = net.get('h1')
    hosts = [h1] + [net.get(f'h{i}') for i in range(2, 16)]

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