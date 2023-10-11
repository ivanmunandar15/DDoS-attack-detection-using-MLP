from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

import topologi_kontroler
from datetime import datetime

import os
import pandas as pd
from sklearn.preprocessing import StandardScaler

from keras.models import load_model

class SimpleMonitor13(topologi_kontroler.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

        start = datetime.now()
        self.flow_training()  # Panggil metode flow_training untuk melatih model
        end = datetime.now()
        print("Waktu Pelatihan: ", (end-start))



    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])

    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

            self.flow_predict()

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):

        timestamp = datetime.now()
        timestamp = timestamp.timestamp()

        file0 = open("PredictFlowStatsfile.csv","w")
        file0.write('timestamp,datapath_id,flow_id,ip_src,tp_src,ip_dst,tp_dst,ip_proto,icmp_code,icmp_type,flow_duration_sec,flow_duration_nsec,idle_timeout,hard_timeout,flags,packet_count,byte_count,packet_count_per_second,packet_count_per_nsecond,byte_count_per_second,byte_count_per_nsecond\n')
        body = ev.msg.body
        icmp_code = -1
        icmp_type = -1
        tp_src = 0
        tp_dst = 0

        for stat in sorted([flow for flow in body if (flow.priority == 1) ], key=lambda flow:
            (flow.match['eth_type'],flow.match['ipv4_src'],flow.match['ipv4_dst'],flow.match['ip_proto'])):
        
            ip_src = stat.match['ipv4_src']
            ip_dst = stat.match['ipv4_dst']
            ip_proto = stat.match['ip_proto']
            
            if stat.match['ip_proto'] == 1:
                icmp_code = stat.match['icmpv4_code']
                icmp_type = stat.match['icmpv4_type']
                
            elif stat.match['ip_proto'] == 6:
                tp_src = stat.match['tcp_src']
                tp_dst = stat.match['tcp_dst']

            elif stat.match['ip_proto'] == 17:
                tp_src = stat.match['udp_src']
                tp_dst = stat.match['udp_dst']

            flow_id = str(ip_src) + str(tp_src) + str(ip_dst) + str(tp_dst) + str(ip_proto)
          
            try:
                packet_count_per_second = stat.packet_count/stat.duration_sec
                packet_count_per_nsecond = stat.packet_count/stat.duration_nsec
            except:
                packet_count_per_second = 0
                packet_count_per_nsecond = 0
                
            try:
                byte_count_per_second = stat.byte_count/stat.duration_sec
                byte_count_per_nsecond = stat.byte_count/stat.duration_nsec
            except:
                byte_count_per_second = 0
                byte_count_per_nsecond = 0
                
            file0.write("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n"
                .format(timestamp, ev.msg.datapath.id, flow_id, ip_src, tp_src,ip_dst, tp_dst,
                        stat.match['ip_proto'],icmp_code,icmp_type,
                        stat.duration_sec, stat.duration_nsec,
                        stat.idle_timeout, stat.hard_timeout,
                        stat.flags, stat.packet_count,stat.byte_count,
                        packet_count_per_second,packet_count_per_nsecond,
                        byte_count_per_second,byte_count_per_nsecond))
            
        file0.close()

    def flow_training(self):
        self.logger.info("Pelatihan Model ...")

        # Periksa apakah file model ada, dan jika ada, muat modelnya
        if os.path.isfile('keras_model.h5'):
            self.flow_model = load_model('keras_model.h5')
        else:
            flow_dataset = pd.read_csv('FlowStatsfile.csv')
            flow_dataset.iloc[:, 2] = flow_dataset.iloc[:, 2].str.replace('.', '')
            flow_dataset.iloc[:, 3] = flow_dataset.iloc[:, 3].str.replace('.', '')
            flow_dataset.iloc[:, 5] = flow_dataset.iloc[:, 5].str.replace('.', '')

            X_flow = flow_dataset.iloc[:, :-1].values
            X_flow = X_flow.astype('float64')

            y_flow = flow_dataset.iloc[:, -1].values

            X_flow_train, X_flow_test, y_flow_train, y_flow_test = train_test_split(X_flow, y_flow, test_size=0.25, random_state=0)

            # Normalisasi data
            scaler = StandardScaler()
            X_flow_train = scaler.fit_transform(X_flow_train)
            X_flow_test = scaler.transform(X_flow_test)

            # Modifikasi model untuk klasifikasi multiclass
            from keras.utils import to_categorical
            y_flow_train = to_categorical(y_flow_train, num_classes=5)
            y_flow_test = to_categorical(y_flow_test, num_classes=5)

            # Inisialisasi model keras
            self.flow_model = Sequential()
            self.flow_model.add(Dense(256, input_dim=X_flow_train.shape[1], activation='relu'))
            self.flow_model.add(Dense(128, activation='relu'))
            self.flow_model.add(Dense(5, activation='softmax'))

            self.flow_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

            # Train the model
            self.flow_model.fit(X_flow_train, y_flow_train, epochs=15, batch_size=batch_size, validation_data=(X_flow_test, y_flow_test))

            # Simpan model setelah pelatihan
            self.flow_model.save('keras_model.h5')

            # Evaluasi model
            _, accuracy = self.flow_model.evaluate(X_flow_test, y_flow_test)
            self.logger.info("Akurasi Model: {:.2f}%".format(accuracy * 100))
                
    def flow_predict(self):
        try:
            predict_flow_dataset = pd.read_csv('PredictFlowStatsfile.csv')
            predict_flow_dataset.iloc[:, 2] = predict_flow_dataset.iloc[:, 2].str.replace('.', '')
            predict_flow_dataset.iloc[:, 3] = predict_flow_dataset.iloc[:, 3].str.replace('.', '')
            predict_flow_dataset.iloc[:, 5] = predict_flow_dataset.iloc[:, 5].str.replace('.', '')
            
            # Praproses data prediksi
            scaler = StandardScaler()
            X_predict_flow = scaler.fit_transform(predict_flow_dataset.iloc[:, :].values.astype('float64'))

            # Prediksi menggunakan model
            predictions = self.flow_model.predict(X_predict_flow)
            
            # Mengambil kelas dengan probabilitas tertinggi sebagai prediksi
            predicted_classes = predictions.argmax(axis=1)
            
            # Menentukan jenis serangan DDoS berdasarkan kelas prediksi
            attack_types = ['Normal', 'ICMP Flood', 'UDP Flood', 'TCP SYN Flood', 'DNS Amplification']
            
            self.logger.info("------------------------------------------------------------------------------")
            if (legitimate_traffic / len(predicted_classes) * 100) > 80:
                self.logger.info("Legitimate traffic detected.")
            else:
                self.logger.info("DDoS traffic detected.")
                for i, count in enumerate(predicted_classes):
                    if count < len(attack_types):
                        victim = int(predict_flow_dataset.iloc[i, 5]) % 20
                        attack_type = attack_types[count]
                        self.logger.info("Victim for class {}: host h{}, Attack Type: {}".format(i, victim, attack_type))
                    else:
                        self.logger.info("Victim for class {}: host h{}, Attack Type: Unknown".format(i, victim))

            self.logger.info("------------------------------------------------------------------------------")

            # Membuka kembali file untuk direset
            file0 = open("PredictFlowStatsfile.csv", "w")
            file0.write(
                'timestamp,datapath_id,flow_id,ip_src,tp_src,ip_dst,tp_dst,ip_proto,icmp_code,icmp_type,flow_duration_sec,flow_duration_nsec,idle_timeout,hard_timeout,flags,packet_count,byte_count,packet_count_per_second,packet_count_per_nsecond,byte_count_per_second,byte_count_per_nsecond\n')
            file0.close()

        except Exception as e:
            self.logger.error("Error in flow prediction: {}".format(e))