from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.node import OVSKernelSwitch, RemoteController
from datetime import datetime
import random, threading, time

class MyTopo(Topo):
    def build(self):
        switches = []
        hosts = []

        for s in range(1, 6):
            switch_name = f's{s}'
            switch = self.addSwitch(switch_name, cls=OVSKernelSwitch, protocols='OpenFlow13')
            switches.append(switch)

            for h in range(1, 4):
                host_id = s * 3 + h - 3
                host_name = f'h{host_id}'
                host_ip = f'10.0.{s}.{h}/24'
                host_mac = f'00:00:00:00:00:{host_id:02d}'
                host = self.addHost(host_name, cpu=1.0/20, mac=host_mac, ip=host_ip)
                hosts.append(host)
                self.addLink(host, switch)

        for i in range(len(switches) - 1):
            self.addLink(switches[i], switches[i + 1])

def ip_generator():
    return f"10.0.{random.randint(1, 5)}.{random.randint(1, 3)}"

def generate_traffic(src, dst, h1_ip):
    print(f"Generating ICMP traffic between {src} and {dst} and TCP/UDP traffic between {src} and h1")
    src.cmd(f"ping {dst} -c 10 &")
    src.cmd(f"iperf -p 5050 -c {h1_ip}")
    src.cmd(f"iperf -p 5051 -u -c {h1_ip}")

    print(f"{src} Downloading index.html from h1")
    src.cmd(f"wget http://{h1_ip}/index.html")
    print(f"{src} Downloading test.zip from h1")
    src.cmd(f"wget http://{h1_ip}/test.zip")

def startNetwork():
    topo = MyTopo()
    c0 = RemoteController('c0', ip='127.0.0.1', port=6653)
    net = Mininet(topo=topo, link=TCLink, controller=c0)
    net.start()

    hosts = net.hosts
    h1_ip = '10.0.0.1'

    for i in range(600):
        print("--------------------------------------------------------------------------------")
        print(f"Iteration n {i+1} ...")
        print("--------------------------------------------------------------------------------")

        threads = []
        for j in range(10):
            src = random.choice(hosts)
            dst = ip_generator()

            thread = threading.Thread(target=generate_traffic, args=(src, dst, h1_ip))
            thread.start()
            threads.append(thread)

            time.sleep(0.5)

        for t in threads:
            t.join()

        net.hosts[0].cmd("rm -f /home/mininet/Downloads/*.*")

    print("--------------------------------------------------------------------------------")
    net.stop()

if __name__ == '__main__':
    start = datetime.now()
    setLogLevel('info')
    startNetwork()
    end = datetime.now()
    print(f"Total time: {end - start}")