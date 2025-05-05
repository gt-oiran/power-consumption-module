#!/bin/bash

echo "Script initialized at $(date)"

source configuration.conf
source script.conf

DATETIME=$(date +%Y%m%d-%H%M%S)
it=$((n * i_time + n * p_time + warmup_time))

mkdir -pv "$FOLDER_NAME/$DIR_TURBOSTAT"
mkdir -pv "$DIR_POWERTOP/$DATETIME/"
mkdir -pv "$FOLDER_NAME/$DIR_RESULT_TS"
mkdir -pv "$FOLDER_NAME/$DIR_RESULT_PT"
PATH_TURBOSTAT="../$FOLDER_NAME/$DIR_TURBOSTAT/turbostat-$DATETIME.csv"
PATH_POWERTOP="../$FOLDER_NAME/$DIR_POWERTOP/$DATETIME"
PATH_RESULT_TS="../$FOLDER_NAME/$DIR_RESULT_TS/result_turbostat-$DATETIME.csv"
PATH_RESULT_PT="../$FOLDER_NAME/$DIR_RESULT_PT/result_powertop-$DATETIME"

echo "Iperf server starting"
docker exec -d $container_name iperf -s -p $port -e -i 1  --sum-only

echo "Measurements started at $(date)"
sudo turbostat --show Time_Of_Day_Seconds,PkgWatt --interval $time --num_iterations $((it / time)) --quiet --Summary --out "$PATH_TURBOSTAT" &> /dev/null &
sudo powertop --csv="$PATH_POWERTOP" --time=$time --iteration=$((it / time)) &> /dev/null &

echo "Warmup period" 
sleep $warmup_time

t=3
for i in $(seq 1 $n) ; do
    t=$((t + 1)) 
    b=$((i*5)) 
    echo "Iniciando teste de Iperf numero: $i , BandWidth: $b M"
    echo "Teste $i - $(date +%Y%m%d-%H%M%S)" >> "$output_file"
    echo $PASSWORD |sudo -S ip netns exec $ue_namespace iperf -c $target_ip -P $p_clients -b $b'M' -t $i_time >> "$output_file"
    sleep $p_time 
done 

wait $(pidof turbostat)
wait $(pidof powertop)

echo "Measurements completed at $(date)"

echo "Processing the data at $(date)"
python3 csv_turbostat.py $PATH_TURBOSTAT $PATH_RESULT_TS $SAMPLES
python3 csv_powertop.py $PATH_POWERTOP $PATH_RESULT_PT $SAMPLES

echo "Script finished at $(date)"