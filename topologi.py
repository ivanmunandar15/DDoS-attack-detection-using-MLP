from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController

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

def startNetwork():
    topo = MyTopo()
    c0 = RemoteController('c0', ip='127.0.0.1')
    net = Mininet(topo=topo, link=TCLink, controller=c0)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    startNetwork()
