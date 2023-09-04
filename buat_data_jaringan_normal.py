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

            print("generating ICMP traffic between %s and h%s and TCP/UDP traffic between %s and h1" % (src, ((dst.split('.'))[3]), src))
            src.cmd("ping {} -c 100 &".format(dst))
            src.cmd("iperf -p 5050 -c 10.0.0.1")
            src.cmd("iperf -p 5051 -u -c 10.0.0.1")

            print("%s Downloading index.html from h1" % src)
            src.cmd("wget http://10.0.0.1/index.html")
            print("%s Downloading test.zip from h1" % src)
            src.cmd("wget http://10.0.0.1/test.zip")

        h1.cmd("rm -f *.* /home/mininet/Downloads")

    print("--------------------------------------------------------------------------------")

    net.stop()

if __name__ == '__main__':
    start = datetime.now()

    setLogLevel('info')
    startNetwork()

    end = datetime.now()

    print(end - start)