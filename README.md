# Power-consumption-module
This README provides a tutorial on how to deploy a gNB-focused environment and xApps using srsRAN. It also outlines the necessary steps to extend the set of metrics collected via E2SM-KPM.

This tutorial is based on the following architecture:
![Env-Architecture](https://github.com/gt-oiran/power-consumption-module/blob/main/Images/architecture.png)

> [!WARNING]  
> This repository includes only the modified files necessary to run this environment. You will need to integrate them with the full srsRAN and O-RAN software stack as described in the tutorial.

## Build tools and dependencies
Before getting started, install the required system dependencies:
```bash
sudo apt-get install cmake make gcc g++ pkg-config libfftw3-dev libmbedtls-dev libsctp-dev libyaml-cpp-dev libgtest-dev build-essential libboost-program-options-dev libconfig++-dev libsctp-dev
```
Next, install ZeroMQ dependencies.

First, libzmq:
```bash
git clone https://github.com/zeromq/libzmq.git
cd libzmq
./autogen.sh
./configure
make
sudo make install
sudo ldconfig
```
Second, czmq:
```bash
git clone https://github.com/zeromq/czmq.git
cd czmq
./autogen.sh
./configure
make
sudo make install
sudo ldconfig
```
## Instalation
This section provides a step-by-step guide to installing all the necessary software components required to set up the environment.
### srsRAN Project
First, clone our extended srsRAN Project repository on both server-1 and server-2:
```bash
git clone [https://github.com/srsran/srsRAN_Project.git](https://github.com/gt-oiran/srsran)
cd srsran
mkdir build
cd build
cmake ../ -DENABLE_EXPORT=ON -DENABLE_ZEROMQ=ON
make -j`nproc`
```

Pay extra attention to the cmake console output. Make sure you read the following line:

```bash
  ...
  -- FINDING ZEROMQ.
  -- Checking for module 'ZeroMQ'
  --   No package 'ZeroMQ' found
  -- Found libZEROMQ: /usr/local/include, /usr/local/lib/libzmq.so
  ...
```
### srsRAN UE
To utilize srsRAN UE, firs we need to download and build srsRAN 4G project on server-1:
```bash
git clone https://github.com/srsRAN/srsRAN_4G.git
cd srsRAN_4G
mkdir build
cd build
cmake ../
make
make test
```
### ORAN-SC-RIC
In this tutorial, we use a modified version of the ORAN-SC RIC based on the i-release provided by srsRAN, to simplify deployment and ensure replicability.

Download the repository on server-1:
```bash
git clone https://github.com/srsran/oran-sc-ric
```

## Configuration
After successfully cloning and installing the srsRAN projects and their respective releases, the next step is to configure communication between the various components.

Fist step is to configure ``gnb_zmq.yaml`` on server-2  and ``ue_zmq.conf`` on server-1.

### gNB
On gNB the user must add to ``bind_addr``, the desired ip:
```yaml
cu_cp:
  amf:
    addr: 10.53.1.2                # The address or hostname of the AMF.
    port: 38412
    bind_addr: 192.168.0.10           # A local IP that the gNB binds to for traffic from the AMF.
...
```
additionally, on ``addr`` and ``bind_addr`` from ``e2`` camp:
```yaml
...
e2:
  enable_du_e2: true                # Enable DU E2 agent (one for each DU instance)
  e2sm_kpm_enabled: true            # Enable KPM service module
  e2sm_rc_enabled: true             # Enable RC service module
  addr: 192.168.0.11                    # RIC IP address
  bind_addr: 192.168.0.10            # A local IP that the E2 agent binds to for traffic from the RIC. ONLY required if running the RIC on a separate machine. 
  port: 36421  
...                     # RIC port
  ```
on ``ru_sdr``, the `device_args` argument needs to address the correct IPs:
```yaml
...
ru_sdr:
  device_driver: zmq                # The RF driver name.
  device_args: tx_port=tcp://192.168.0.10:2000,rx_port=tcp://192.168.0.11:2001,base_srate=11.52e6 # Optionally pass arguments to the selected RF driver.
  srate: 11.52                      # RF sample rate might need to be adjusted according to selected bandwidth.
  tx_gain: 75                       # Transmit gain of the RF might need to adjusted to the given situation.
  rx_gain: 75                       # Receive gain of the RF might need to adjusted to the given situation.
...
```
Also, a direct route between gNB server-2 and Core (on server-1), needs to be configured in server-2 as:
```bash
sudo ip route add 10.53.1.0/24 via 192.168.0.11
```
If facing connections problems, the user can disable firewall, by:
```bash
sudo upf disable
```
### UE
On srsRAN 4g Project, the ``ue_zmq.conf`` need to be altered, following the proposed architecture:
```conf
[rf]
freq_offset = 0
tx_gain = 50
rx_gain = 40
srate = 11.52e6
nof_antennas = 1

device_name = zmq
device_args = tx_port=tcp://192.168.0.11:2001,rx_port=tcp://192.168.0.10:2000,base_srate=11.52e6
...
```
The field usim, is responsible for providing authentication info to AMF core function.
```conf
[usim]
mode = soft
algo = milenage
opc  = 63BFA50EE6523365FF14C1F45F88737D
k    = 00112233445566778899aabbccddeeff
imsi = 001010123456780
imei = 353490069873319
```
If one needs to configure AMF database, the following file have to be modified: ``./srsRAN_Project/docker/open5gs/open5gs.env``, 

### ORAN-SC-RIC
The communication between near-rt-ric and gNB needs to be secured by altering the ``docker-compose.yml`` file on ``./oran-sc-ric``:
```yml
 e2term:
    container_name: ric_e2term
    hostname: e2term
    image: nexus3.o-ran-sc.org:10002/o-ran-sc/ric-plt-e2:${E2TERM_VER}
    #Uncomment ports to use the RIC from outside the docker network.
    ports:
      - "36421:36421/sctp"
```
## Running the project
The following order should be used when running the network:

- Open5GS
- ORAN-SC-RIC
- gNB
- UE
- xApp

### Open5gs
In this scenario, we use a dockerized version of open5gs provided by srsRAN

The project can be run as:
```bash
cd ./srsRAN_Project/docker
docker compose up 5gc
```
Alternativelly, if facing problems during docker compose, one can use ``--build`` flag:
```bash
docker compose up --build 5gc
```
### ORAN-SC-RIC
The ``release-i`` of near-rt-ric, can be run as 
```bash
cd ./oran-sc-ric
docker compose up
```
the flag ``--build`` can also be used if needed

After sucessfully installing (if run for the first time) and running the containers, the console output shoud present the message:
```bash
ric_submgr          | RMR is ready now ...
```
### gNB
After running open-5gs and near-rt-ric, the gnb can be run as:

```bash
cd ./srsRAN_Project/build/apps/gnb
sudo ./gnb -c gnb_zmq.yaml
```
The console shoud present a message similar to:
```bash
--== srsRAN gNB (commit 9d5dd742a) ==--


The PRACH detector will not meet the performance requirements with the configuration {Format 0, ZCZ 0, SCS 1.25kHz, Rx ports 1}.
Lower PHY in executor blocking mode.
E2AP: Connection to Near-RT-RIC on 192.168.0.11:36421 completed
Available radio types: zmq.
Cell pci=1, bw=10 MHz, 1T1R, dl_arfcn=368500 (n3), dl_freq=1842.5 MHz, dl_ssb_arfcn=368410, ul_freq=1747.5 MHz

N2: Connection to AMF on 10.53.1.2:38412 completed
==== gNB started ===
Type <h> to view help
```
Additionally, the open-5gs output should recognize the added gnb, such as:
```bash
open5gs_5gc  | 05/05 04:49:40.521: [amf] INFO: gNB-N2 accepted[192.168.0.10]:41990 in ng-path module (../src/amf/ngap-sctp.c:113)
open5gs_5gc  | 05/05 04:49:40.521: [amf] INFO: gNB-N2 accepted[192.168.0.10] in master_sm module (../src/amf/amf-sm.c:741)
open5gs_5gc  | 05/05 04:49:40.532: [amf] INFO: [Added] Number of gNBs is now 1 (../src/amf/context.c:1231)
open5gs_5gc  | 05/05 04:49:40.532: [amf] INFO: gNB-N2[192.168.0.10] max_num_of_ostreams : 30 (../src/amf/amf-sm.c:780)
```
### UE
Before running srsRAN_4g project, we need to create network namespace for the ue on server-1, the name should be the same as specified in ``[gw]`` field from ``gnb_zmq.conf``
```bash
sudo ip netns add ue1
```
Now the project can be run: 
```bash
cd ./srsRAN_4G/build/srsue/src
sudo ./srsue ue_zmq.conf
```
The console should present the following:
```bash 
Active RF plugins: libsrsran_rf_zmq.so
Inactive RF plugins: 
Reading configuration file ue_zmq_sep.conf...

Built in Release mode using commit ec29b0c1f on branch master.

Opening 1 channels in RF device=zmq with args=tx_port=tcp://192.168.0.11:2001,rx_port=tcp://192.168.0.10:2000,base_srate=11.52e6
Supported RF device list: zmq file
CHx base_srate=11.52e6
Current sample rate is 1.92 MHz with a base rate of 11.52 MHz (x6 decimation)
CH0 rx_port=tcp://192.168.0.10:2000
CH0 tx_port=tcp://192.168.0.11:2001
Current sample rate is 11.52 MHz with a base rate of 11.52 MHz (x1 decimation)
Current sample rate is 11.52 MHz with a base rate of 11.52 MHz (x1 decimation)
Waiting PHY to initialize ... done!
Attaching UE...
Random Access Transmission: prach_occasion=0, preamble_index=0, ra-rnti=0x39, tti=174
Random Access Complete.     c-rnti=0x4601, ta=0
RRC Connected
PDU Session Establishment successful. IP: 10.45.1.2
RRC NR reconfiguration successful.
```
### xAPP
From the dir ``./oran-sc-ric``, is possible to run xApps contained in the folder ``./oran-sc-ric/xApps``, the following command execute them:
```bash 
docker compose exec python_xapp_runner ./oranor_xapp.py --<flag>
```
Some flags examples:

- ``--metrics`` : Name the metrics for collection. Comma separated strings for various metrics.

- ``--buffer`` : Defines the buffer size in seconds

- ``--model`` : Select the model from ./oran-sc-ric/xApps/python/models

## New metrics for srsRAN
New metrics implementation includes:
- uplink SNR on PUSCH (dB) - ``SNR``
- Physical Cell Id - ``PCI``
- Modulation and coding scheme (Uplink and Donwlink, kbps) - ``McsUl`` ``McsDl``
- Bitrate per Direction (Uplink and Donwlink, kbps) - ``BrateUl``, ``BrateDl``
- Number of successful and failed transport blocks (Uplink and Donwlink) - ``NofOKUl``,``NofOKDl``,``NofNOKUl``,``NofNOKDl``
- Buffer Status Report - ``BSR``
- Downlink buffer size - ``BSDl``
- Timing Advance (nanoseconds) - ``TA``
- Power Headroom Report (dB) -  ``PHR``
- Rank Indicator - ``RI``

### Implementation:
To utilize the new metrics in the srsRAN framework, the following modifications to the E2SM-KPM (E2 Service Management for Key Performance Metrics) functions are necessary. Specifically, we will modify the getter functions located in the ./srsRAN_Project/lib/e2/e2sm/e2sm_kpm directory.

Example: SNR Metric

1 - First, we add the method responsible to colect the SNR metric in  ``e2sm_kpm_du_meas_provider_impl.h``:

```c++
metric_meas_getter_func_t get_pusch_snr;
```
2 - In the ``e2sm_kpm_du_meas_provider_impl.cpp`` file, add the SNR metric to the supported_metrics array. This will associate the metric name (SNR) with the relevant getter function and other necessary details, such as supported labels and levels, and whether cell-scoping is supported:

```c++
supported_metrics.emplace(
      "SNR", e2sm_kpm_supported_metric_t{supported_labels, supported_levels, cell_scope_supported, &e2sm_kpm_du_meas_provider_impl::get_pusch_snr});
```
And also, implement the function that collects the SNR metric. This function is responsible for extracting the metric value and storing it in the items vector:

```c++
bool e2sm_kpm_du_meas_provider_impl::get_pusch_snr(const asn1::e2sm::label_info_list_l          label_info_list,
                                            const std::vector<asn1::e2sm::ue_id_c>&      ues,
                                            const std::optional<asn1::e2sm::cgi_c>       cell_global_id,
                                            std::vector<asn1::e2sm::meas_record_item_c>& items)
{
  bool                 meas_collected = false;
  scheduler_ue_metrics ue_metrics     = last_ue_metrics[0];

  meas_record_item_c meas_record_item;
  meas_record_item.set_integer() = (int)ue_metrics.pusch_snr_db;  // logic of collection
  items.push_back(meas_record_item);
  meas_collected = true;

  return meas_collected;
}
```
This function collects the SNR value from the scheduler_ue_metrics structure (specifically, the pusch_snr_db field), converts it to an integer, and stores it in the items vector for further processing.


4 - If needed, you can further customize the logic for collecting other metrics or adjust existing ones based on the requirements. The relevant scheduling metrics can be found in the ``./srsRAN_Project/include/srsran/scheduler/scheduler_metrics.h`` file. You can modify these collection methods to match the specific needs of your application.



