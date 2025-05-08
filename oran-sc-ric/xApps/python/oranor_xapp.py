#!/usr/bin/env python3

import argparse
import signal
import numpy as np
import os
import csv
import time
import pickle
import joblib
import xgboost as xgb 
from lib.xAppBase import xAppBase
from sklearn.preprocessing import MinMaxScaler

class MyXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port, model_path):
        super(MyXapp, self).__init__(config, http_server_port, rmr_port)
        model_name = os.path.basename(model_path).replace(".pkl", "")
        self.csv_dir = "./Metrics"  
        self.time_init = time.strftime("%d%m%Y-%H%M%S")
        self.csv_file = f'{model_name}_metrics_{self.time_init}.csv'
        self.written_header = False
        self._initialize_csv()

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        try:
            file_ext = os.path.splitext(model_path)[-1] 

            if file_ext == ".pkl":
                self.model = joblib.load(model_path)
            elif file_ext == ".json":
                self.model = xgb.Booster()
                self.model.load_model(model_path)
            else:
                raise ValueError(f"Formato de modelo não suportado: {file_ext}")

            print(f"Model loaded successfully from {model_path}")

        except Exception as e:
            print(f"Error loading model: {e}")
            raise

        self.buffer_array = []
        self.buffer_ready = False
    
    def _initialize_csv(self):
        # Verifica se o diretório existe, se não, cria
        if not os.path.exists(self.csv_dir):
            os.makedirs(self.csv_dir)
            
        self.csv_path = os.path.join(self.csv_dir, self.csv_file)
        
        # Inicializa o arquivo CSV se não existir
        try:
            with open(self.csv_path, mode='w', newline='') as file:
                pass
        except Exception as e:
            print(f"Error initializing CSV file: {e}")
        
    def my_subscription_callback(self, e2_agent_id, subscription_id, indication_hdr, indication_msg, kpm_report_style, ue_id):
        if kpm_report_style == 2:
            print("\nRIC Indication Received from {} for Subscription ID: {}, KPM Report Style: {}, UE ID: {}".format(e2_agent_id, subscription_id, kpm_report_style, ue_id))
        else:
            print("\nRIC Indication Received from {} for Subscription ID: {}, KPM Report Style: {}".format(e2_agent_id, subscription_id, kpm_report_style))

        indication_hdr = self.e2sm_kpm.extract_hdr_info(indication_hdr)
        meas_data = self.e2sm_kpm.extract_meas_data(indication_msg)
        
        # Creation of necessary variables
        timestamp = time.time()
        name_metrics = list(meas_data["measData"].keys())
        metric_values = list(meas_data["measData"].values())
        self.get_data(meas_data) 
        
        print("E2SM_KPM RIC Indication Content:")
        print("-ColletStartTime: ", indication_hdr['colletStartTime'])
        print("-Measurements Data:")

        granulPeriod = meas_data.get("granulPeriod", None)
        if granulPeriod is not None:
            print("-granulPeriod: {}".format(granulPeriod))

        if kpm_report_style in [1,2]:
            for metric_name, value in meas_data["measData"].items():
                print("--Metric: {}, Value: {}".format(metric_name, value))

        else:
            for ue_id, ue_meas_data in meas_data["ueMeasData"].items():
                print("--UE_id: {}".format(ue_id))
                granulPeriod = ue_meas_data.get("granulPeriod", None)
                if granulPeriod is not None:
                    print("---granulPeriod: {}".format(granulPeriod))

                for metric_name, value in ue_meas_data["measData"].items():
                    print("---Metric: {}, Value: {}".format(metric_name, value))
        
        if self.buffer_ready == True:
            prediction = self.energy_predictor(self.features)
        
        # CSV writer
        with open(self.csv_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            
            if not self.written_header:
                header = ["Timestamp", "E2 Agent ID", "Subscription ID"] + name_metrics + ["PowerPrediction"] + ["Airtime_Norm"] + ["SNR_Norm"] + ["Mcs_Norm"] #+ ["Metrics Array"] 
                writer.writerow(header)
                self.written_header = True
            
            flat_metric_values = [value[0] if isinstance(value, list) else value for value in metric_values] 
            
            if self.buffer_ready == True:  
                #flat_prediction = [prediction[0][0] if isinstance(prediction[0], list) else prediction[0]]
                flat_prediction = prediction[0][0] if isinstance(prediction[0], (list, np.ndarray)) else prediction[0]
                #writer.writerow([timestamp, e2_agent_id, subscription_id]+ flat_metric_values + list(flat_prediction[0]) ) #+ [self.metric_array] + [self.features] )
                writer.writerow([timestamp, e2_agent_id, subscription_id]+ flat_metric_values + [flat_prediction] + [self.airtime_scl] + [self.snr_scl]  + [self.mcs_ul_scl]) #+ [self.metric_array] + [self.features] )
            else:     
                writer.writerow([timestamp, e2_agent_id, subscription_id]+ flat_metric_values + ["NA"] ) #+ [self.metric_array])            
    
    def metrics_buffer(self, metric_array):
        ts = time.time()
        self.buffer_array.append((metric_array,ts))
        
        last_timestamp = self.buffer_array[-1][1]
        self.buffer_array = [
            item for item in self.buffer_array
            if (last_timestamp - item[1]) <= buffer + 1
        ]
        ##print(f"\n\n BUFFER:{self.buffer_array}\n\n")
        if len(self.buffer_array)> 1:    
            time_diff  = (self.buffer_array[-1][1] - self.buffer_array[0][1])

            if (time_diff) >= buffer:
                # print(f"\n\n BUFFER:{self.buffer_array}\n\n")
                self.normalize_features(self.buffer_array)           
                self.buffer_ready = True
    
        #

            
    def get_data(self, meas_data):
        mcs_ul = meas_data["measData"].get("McsUl")
        snr = meas_data["measData"].get("SNR")
        prbtotul = meas_data["measData"].get("RRU.PrbTotUl") # This measurement provides the total usage (in percentage) of physical resource blocks (PRBs)
        prbmeanul = meas_data["measData"].get("RRU.PrbUsedUl")

        # conversion to expected format 
        if isinstance(mcs_ul, list):
            mcs_ul = mcs_ul[0]
        if isinstance(snr, list):
            snr = snr[0]
        if isinstance(prbtotul, list):
            prbtotul = prbtotul[0]
        if isinstance(prbmeanul, list):
            prbmeanul = prbmeanul[0]
        
        self.metric_array = [mcs_ul, snr, prbtotul]#
        self.metrics_buffer(self.metric_array)



    def normalize_features(self, buffer_array):
        # Extracting the means of columns
        array = [items[0] for items in buffer_array]
        buffer_array = np.array(array)
        mean_mcs_ul = np.mean(buffer_array[:, 2])
        mean_snr = np.mean(buffer_array[:, 1])
        mean_prbtotul = np.mean(buffer_array[:, 0])

        airtime = mean_prbtotul / 100
        
        airtime_ul_max = 1
        airtime_ul_min = 0
        mcs_ul_max = 28
        mcs_ul_min = 0
        snr_max = 65
        snr_min = 0

        # Metrics normalization        
        mcs_ul_norm = (mean_mcs_ul - mcs_ul_min) / (mcs_ul_max - mcs_ul_min)
        self.mcs_ul_scl = mcs_ul_norm*(mcs_ul_max - mcs_ul_min) + mcs_ul_min
        snr_norm = (mean_snr - snr_min) / (snr_max - snr_min)
        self.snr_scl = snr_norm*(snr_max - snr_min) + snr_min
        airtime_norm = (airtime - airtime_ul_min) / (airtime_ul_max - airtime_ul_min)
        self.airtime_scl = airtime_norm*(airtime_ul_max - airtime_ul_min) + airtime_ul_min
        
        # Array construction
        self.features = np.array([[self.airtime_scl,self.snr_scl,self.mcs_ul_scl]]) # 2 - 
        # print(f"\n\n Features:{self.features}\n\n")
        # print(type(self.features))
        self.energy_predictor(self.features)
        
    
    def energy_predictor(self, features): 
        # Make power predictions based on provided features  
        prediction = self.model.predict(self.features)
        time_diff  = (self.buffer_array[-1][1] - self.buffer_array[0][1])
        print(f"Estimated Power: {prediction[0].item():.4f} W  Estimated Energy : {prediction[0].item() * (1/3600):.4f} Wh")
        # print(f"Power Estimated: {prediction[0].item()}W  Energy Estimated: {prediction[0].item() * (self.time_init - time.strftime("%d%m%Y-%H%M%S")) * (10**-3)}kW/h")
        return prediction          

    # Mark the function as xApp start function using xAppBase.start_function decorator.
    # It is required to start the internal msg receive loop.
    @xAppBase.start_function
    def start(self, e2_node_id, kpm_report_style, ue_ids, metric_names):
        report_period = 1000
        granul_period = 1000

        # use always the same subscription callback, but bind kpm_report_style parameter
        subscription_callback = lambda agent, sub, hdr, msg: self.my_subscription_callback(agent, sub, hdr, msg, kpm_report_style, None)

        if (kpm_report_style == 1):
            print("Subscribe to E2 node ID: {}, RAN func: e2sm_kpm, Report Style: {}, metrics: {}".format(e2_node_id, kpm_report_style, metric_names))
            self.e2sm_kpm.subscribe_report_service_style_1(e2_node_id, report_period, metric_names, granul_period, subscription_callback)

        elif (kpm_report_style == 2):
            # need to bind also UE_ID to callback as it is not present in the RIC indication in the case of E2SM KPM Report Style 2
            subscription_callback = lambda agent, sub, hdr, msg: self.my_subscription_callback(agent, sub, hdr, msg, kpm_report_style, ue_ids[0])
            
            print("Subscribe to E2 node ID: {}, RAN func: e2sm_kpm, Report Style: {}, UE_id: {}, metrics: {}".format(e2_node_id, kpm_report_style, ue_ids[0], metric_names))
            self.e2sm_kpm.subscribe_report_service_style_2(e2_node_id, report_period, ue_ids[0], metric_names, granul_period, subscription_callback)

        elif (kpm_report_style == 3):
            if (len(metric_names) > 1):
                metric_names = metric_names[0]
                print("INFO: Currently only 1 metric can be requested in E2SM-KPM Report Style 3, selected metric: {}".format(metric_names))
            # TODO: currently only dummy condition that is always satisfied, useful to get IDs of all connected UEs
            # example matching UE condition: ul-rSRP < 1000
            matchingConds = [{'matchingCondChoice': ('testCondInfo', {'testType': ('ul-rSRP', 'true'), 'testExpr': 'lessthan', 'testValue': ('valueInt', 1000)})}]

            print("Subscribe to E2 node ID: {}, RAN func: e2sm_kpm, Report Style: {}, metrics: {}".format(e2_node_id, kpm_report_style, metric_names))
            self.e2sm_kpm.subscribe_report_service_style_3(e2_node_id, report_period, matchingConds, metric_names, granul_period, subscription_callback)

        elif (kpm_report_style == 4):
            # TODO: currently only dummy condition that is always satisfied, useful to get IDs of all connected UEs
            # example matching UE condition: ul-rSRP < 1000
            matchingUeConds = [{'testCondInfo': {'testType': ('ul-rSRP', 'true'), 'testExpr': 'lessthan', 'testValue': ('valueInt', 1000)}}]
            
            print("Subscribe to E2 node ID: {}, RAN func: e2sm_kpm, Report Style: {}, metrics: {}".format(e2_node_id, kpm_report_style, metric_names))
            self.e2sm_kpm.subscribe_report_service_style_4(e2_node_id, report_period, matchingUeConds, metric_names, granul_period, subscription_callback)

        elif (kpm_report_style == 5):
            if (len(ue_ids) < 2):
                dummyUeId = ue_ids[0] + 1
                ue_ids.append(dummyUeId)
                print("INFO: Subscription for E2SM_KPM Report Service Style 5 requires at least two UE IDs -> add dummy UeID: {}".format(dummyUeId))

            print("Subscribe to E2 node ID: {}, RAN func: e2sm_kpm, Report Style: {}, UE_ids: {}, metrics: {}".format(e2_node_id, kpm_report_style, ue_ids, metric_names))
            self.e2sm_kpm.subscribe_report_service_style_5(e2_node_id, report_period, ue_ids, metric_names, granul_period, subscription_callback)

        else:
            print("INFO: Subscription for E2SM_KPM Report Service Style {} is not supported".format(kpm_report_style))
            exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My example xApp')
    parser.add_argument("--config", type=str, default='', help="xApp config file path")
    parser.add_argument("--http_server_port", type=int, default=8092, help="HTTP server listen port")
    parser.add_argument("--rmr_port", type=int, default=4562, help="RMR port")
    parser.add_argument("--e2_node_id", type=str, default='gnbd_001_001_00019b_0', help="E2 Node ID")
    parser.add_argument("--ran_func_id", type=int, default=2, help="RAN function ID")
    parser.add_argument("--kpm_report_style", type=int, default=1, help="xApp config file path")
    parser.add_argument("--ue_ids", type=str, default='0', help="UE ID")
    parser.add_argument("--metrics", type=str, default='RRU.PrbAvailUl,RRU.PrbTotUl,McsUl,SNR', help="Metrics name as comma-separated string")
    parser.add_argument("--buffer_size", type=int, default='60', help="Defines the size buffer will have")
    parser.add_argument("--model", type=str, default='/opt/xApps/models/decision_tree_12-02-2025_01-05-59_5.pkl', help="Select the model to use. (default path: /opt/xApps/models/<model_name>)")

    args = parser.parse_args()
    config = args.config
    e2_node_id = args.e2_node_id # TODO: get available E2 nodes from SubMgr, now the id has to be given.
    ran_func_id = args.ran_func_id # TODO: get available E2 nodes from SubMgr, now the id has to be given.
    ue_ids = list(map(int, args.ue_ids.split(","))) # Note: the UE id has to exist at E2 node!
    kpm_report_style = args.kpm_report_style
    metrics = args.metrics.split(",")
    buffer = args.buffer_size
    model_path= args.model

    # Create MyXapp.
    myXapp = MyXapp(config, args.http_server_port, args.rmr_port, args.model)
    myXapp.e2sm_kpm.set_ran_func_id(ran_func_id)

    # Connect exit signals.
    signal.signal(signal.SIGQUIT, myXapp.signal_handler)
    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    # Start xApp.
    myXapp.start(e2_node_id, kpm_report_style, ue_ids, metrics)
    # Note: xApp will unsubscribe all active subscriptions at exit.
