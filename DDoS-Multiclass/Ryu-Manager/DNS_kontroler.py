import topologi_kontroler
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
import os
import datetime


class CollectFlowStatsApp(topologi_kontroler.SimpleSwitch13):
    def __init__(self, *args, **kwargs):
        super(CollectFlowStatsApp, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self.monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange, [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
                self.logger.debug('Registered datapath: %016x', datapath.id)

        elif ev.state == CONFIG_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]
                self.logger.debug('Unregistered datapath: %016x', datapath.id)

    def monitor(self):
        while True:
            for datapath in self.datapaths.values():
                self.request_stats(datapath)
            hub.sleep(10)

    def request_stats(self, datapath):
        self.logger.debug('Sending stats request to datapath: %016x', datapath.id)
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    # Fungsi untuk menangani balasan statistik aliran protokol OpenFlow
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def handle_flow_stats_reply(self, event):
        # Mendapatkan stempel waktu saat ini
        timestamp = datetime.now().timestamp()

        # Variabel untuk informasi ICMP, TCP, dan UDP
        icmp_code = -1
        icmp_type = -1
        tp_src = 0
        tp_dst = 0

        # Memastikan folder dataset ada, jika tidak, buat folder tersebut
        dataset_folder = 'dataset'
        os.makedirs(dataset_folder, exist_ok=True)

        # Path file CSV di dalam folder dataset untuk menyimpan statistik aliran
        file_path = os.path.join(dataset_folder, "FlowStatsfile.csv")

        # Menyertakan header jika file belum ada atau kosong
        header = "Timestamp,DatapathID,FlowID,IPSource,PortSource,IPDestination,PortDestination,IPProtocol," \
                "ICMPCode,ICMPType,DurationSecond,DurationNSecond,IdleTimeout,HardTimeout,Flags," \
                "PacketCount,ByteCount,PacketCountPerSecond,PacketCountPerNSecond,ByteCountPerSecond," \
                "ByteCountPerNSecond,Label\n"

        # Membuka atau membuat file CSV di dalam folder dataset untuk menyimpan statistik aliran
        with open(file_path, "a+") as file:
            # Menyertakan header jika file kosong
            if os.path.getsize(file_path) == 0:
                file.write(header)

            # Ekstrak statistik aliran dari pesan acara
            body = event.msg.body
            
            # Menelusuri aliran dengan prioritas 1 dan mengurutkannya berdasarkan kriteria tertentu
            for stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (
                    flow.match['eth_type'], flow.match['ipv4_src'], flow.match['ipv4_dst'], flow.match['ip_proto'])):                    
                           
                ip_src = stat.match['ipv4_src']
                ip_dst = stat.match['ipv4_dst']
                ip_proto = stat.match['ip_proto']

                # Menentukan detail ICMP, TCP, atau UDP berdasarkan protokol IP
                if ip_proto == 1:
                    icmp_code = stat.match['icmpv4_code']
                    icmp_type = stat.match['icmpv4_type']
                elif ip_proto == 6:
                    tp_src = stat.match['tcp_src']
                    tp_dst = stat.match['tcp_dst']
                elif ip_proto == 17:
                    tp_src = stat.match['udp_src']
                    tp_dst = stat.match['udp_dst']

                # Menghasilkan ID aliran unik
                flow_id = str(ip_src) + str(tp_src) + str(ip_dst) + str(tp_dst) + str(ip_proto)

                # Menghitung jumlah paket dan byte per detik dan per nanodetik
                try:
                    packet_count_per_second = stat.packet_count / stat.duration_sec
                    packet_count_per_nsecond = stat.packet_count / stat.duration_nsec
                except:
                    packet_count_per_second = 0
                    packet_count_per_nsecond = 0

                try:
                    byte_count_per_second = stat.byte_count / stat.duration_sec
                    byte_count_per_nsecond = stat.byte_count / stat.duration_nsec
                except:
                    byte_count_per_second = 0
                byte_count_per_nsecond = 0

                # Menulis statistik aliran ke file CSV di dalam folder dataset
                file.write("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                    timestamp, event.msg.datapath.id, flow_id, ip_src, tp_src, ip_dst, tp_dst,
                    ip_proto, icmp_code, icmp_type, stat.duration_sec, stat.duration_nsec,
                    stat.idle_timeout, stat.hard_timeout, stat.flags, stat.packet_count, stat.byte_count,
                    packet_count_per_second, packet_count_per_nsecond, byte_count_per_second, byte_count_per_nsecond, 4))
                
            file.close()

if __name__ == "__main__":
    from ryu.cmd import manager
    manager.main()
