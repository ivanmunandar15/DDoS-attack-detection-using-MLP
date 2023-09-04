from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
import datetime
import topologi


class CollectFlowStatsApp(topologi.SimpleSwitch13):
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
    def flow_stats_reply_handler(self, ev):
        timestamp = datetime.datetime.now().timestamp()
        body = ev.msg.body
        for stat in body:
            flow_id = f"{stat.match['ipv4_src']}-{stat.match['ipv4_dst']}-{stat.match['ip_proto']}-{stat.match['tcp_src']}-{stat.match['tcp_dst']}-{stat.match['udp_src']}-{stat.match['udp_dst']}"
            packet_count_per_second = stat.packet_count / stat.duration_sec if stat.duration_sec > 0 else 0
            byte_count_per_second = stat.byte_count / stat.duration_sec if stat.duration_sec > 0 else 0
            self.save_to_csv(timestamp, ev.msg.datapath.id, flow_id, packet_count_per_second, byte_count_per_second)

    def save_to_csv(self, timestamp, datapath_id, flow_id, packet_count_per_second, byte_count_per_second):
        with open("FlowStats.csv", "a+") as file:
            file.write(f"{timestamp},{datapath_id},{flow_id},{packet_count_per_second},{byte_count_per_second}\n")

if __name__ == "__main__":
    from ryu.cmd import manager
    manager.main()
