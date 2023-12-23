import os
from datetime import datetime
import topologi_kontroler
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

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

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def handle_flow_stats_reply(self, event):
        body = event.msg.body
        timestamp = datetime.now().timestamp()
        dataset_folder = 'dataset'
        os.makedirs(dataset_folder, exist_ok=True)
        file_path = os.path.join(dataset_folder, "FlowStatsfile.csv")

        with open(file_path, "a+") as file:
            if os.path.getsize(file_path) == 0:
                header = "Timestamp,DatapathID,FlowID,IPSource,PortSource,IPDestination,PortDestination,IPProtocol," \
                         "ICMPCode,ICMPType,DurationSecond,DurationNSecond,IdleTimeout,HardTimeout,Flags," \
                         "PacketCount,ByteCount,PacketCountPerSecond,PacketCountPerNSecond,ByteCountPerSecond," \
                         "ByteCountPerNSecond,Label\n"
                file.write(header)

            for stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (
                    flow.match['eth_type'], flow.match.get('ipv4_src', ''), flow.match.get('ipv4_dst', ''), flow.match.get('ip_proto', 0))):
                flow_details = self.parse_flow_stat(stat)
                file.write("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                    timestamp, event.msg.datapath.id, *flow_details))

    def parse_flow_stat(self, stat):
        ip_src = stat.match.get('ipv4_src', '0.0.0.0')
        ip_dst = stat.match.get('ipv4_dst', '0.0.0.0')
        ip_proto = stat.match.get('ip_proto', 0)

        icmp_code, icmp_type, tp_src, tp_dst = -1, -1, 0, 0
        if ip_proto == 1:
            icmp_code = stat.match.get('icmpv4_code', 0)
            icmp_type = stat.match.get('icmpv4_type', 0)
        elif ip_proto == 6:
            tp_src = stat.match.get('tcp_src', 0)
            tp_dst = stat.match.get('tcp_dst', 0)
        elif ip_proto == 17:
            tp_src = stat.match.get('udp_src', 0)
            tp_dst = stat.match.get('udp_dst', 0)

        flow_id = f"{ip_src}:{tp_src}->{ip_dst}:{tp_dst}:{ip_proto}"

        packet_count_per_second, packet_count_per_nsecond, byte_count_per_second, byte_count_per_nsecond = self.calculate_rates(stat)

        return ip_src, tp_src, ip_dst, tp_dst, ip_proto, icmp_code, icmp_type, \
               stat.duration_sec, stat.duration_nsec, stat.idle_timeout, stat.hard_timeout, stat.flags, \
               stat.packet_count, stat.byte_count, packet_count_per_second, packet_count_per_nsecond, \
               byte_count_per_second, byte_count_per_nsecond, 0

    def calculate_rates(self, stat):
        try:
            packet_count_per_second = stat.packet_count / stat.duration_sec if stat.duration_sec else 0
            packet_count_per_nsecond = stat.packet_count / stat.duration_nsec if stat.duration_nsec else 0
            byte_count_per_second = stat.byte_count / stat.duration_sec if stat.duration_sec else 0
            byte_count_per_nsecond = stat.byte_count / stat.duration_nsec if stat.duration_nsec else 0
        except ZeroDivisionError:
            packet_count_per_second = packet_count_per_nsecond = byte_count_per_second = byte_count_per_nsecond = 0

        return packet_count_per_second, packet_count_per_nsecond, byte_count_per_second, byte_count_per_nsecond

if __name__ == "__main__":
    from ryu.cmd import manager
    manager.main()