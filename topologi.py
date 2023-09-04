from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, RemoteController

class MyTopo(Topo):
    def build(self):

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

def startNetwork():
    topo = MyTopo()
    c0 = RemoteController('c0', ip='192.168.0.101', port=6653)
    net = Mininet(topo=topo, link=TCLink, controller=c0)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    startNetwork()
