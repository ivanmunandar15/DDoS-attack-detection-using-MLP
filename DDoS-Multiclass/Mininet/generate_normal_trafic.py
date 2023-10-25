from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import OVSKernelSwitch, RemoteController
from time import sleep
import random

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

    ip = ".".join(["10","0","0",str(randrange(1,16))])
    return ip
        
def startNetwork():

    topo = MyTopo()

    c0 = RemoteController('c0', ip='127.0.0.1')
    net = Mininet(topo=topo, link=TCLink, controller=c0)

    net.start()
    
    hosts = net.hosts
    h1 = hosts[0]

    print("--------------------------------------------------------------------------------")    
    print("Generating traffic ...")    
    h1.cmd('cd /home/mininet/webserver')
    h1.cmd('python -m SimpleHTTPServer 80 &')
    h1.cmd('iperf -s -p 5050 &')
    h1.cmd('iperf -s -u -p 5051 &')
    sleep(2)

    for h in hosts:
        h.cmd('cd /home/mininet/Downloads')

    for i in range(600):
        print("--------------------------------------------------------------------------------")    
        print("Iteration n {} ...".format(i+1))
        print("--------------------------------------------------------------------------------") 
        
        for j in range(10):
            src = choice(hosts)
            dst = ip_generator()
            
            if j <9:
                print("generating ICMP traffic between %s and h%s and TCP/UDP traffic between %s and h1" % (src,((dst.split('.'))[3]),src))
                src.cmd("ping {} -c 100 &".format(dst))
                src.cmd("iperf -p 5050 -c 10.0.0.1")
                src.cmd("iperf -p 5051 -u -c 10.0.0.1")
            else:
                print("generating ICMP traffic between %s and h%s and TCP/UDP traffic between %s and h1" % (src,((dst.split('.'))[3]),src))
                src.cmd("ping {} -c 100".format(dst))
                src.cmd("iperf -p 5050 -c 10.0.0.1")
                src.cmd("iperf -p 5051 -u -c 10.0.0.1")
            
            print("%s Downloading index.html from h1" % src)
            src.cmd("wget http://10.0.0.1/index.html")
            print("%s Downloading test.zip from h1" % src)
            src.cmd("wget http://10.0.0.1/test.zip")
        
        h1.cmd("rm -f *.* /home/mininet/Downloads")
        
    print("--------------------------------------------------------------------------------")  
    
    # CLI(net)
    net.stop()

if __name__ == '__main__':
    
    start = datetime.now()
    
    setLogLevel( 'info' )
    startNetwork()
    
    end = datetime.now()
    
    print(end-start)
