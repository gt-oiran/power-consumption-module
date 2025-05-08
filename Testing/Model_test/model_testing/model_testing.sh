#!/bin/bash
echo "Script initialized at $(date)"
source configuration.conf
source ../../env/env.conf

DATETIME=$(date +%Y%m%d-%H%M%S)
mapfile -t models < <(ssh -o StrictHostKeyChecking=no "$HOST2" "ls -1 $model_dir")
it=$(((n * i_time + n * p_time + warmup_time) + 30))

run_remote() {
    local host="$1"
    local password="$3"
    local command="$2"
    ssh -o StrictHostKeyChecking=no "$host" "echo '$password' | sudo -S bash -c '$command'"
    if [ $? -ne 0 ]; then
        echo "Erro ao executar comando no host $host: $command"
        exit 1
    fi
}

power_test(){
    echo "Measurements started at $(date)"
    run_remote "$HOST1" "turbostat --show Time_Of_Day_Seconds,PkgWatt --interval $time --num_iterations $((it / time)) --quiet --Summary --out $H1_test_dir$PATH_TURBOSTAT &> /dev/null &" "$H1_pwrd" &
    run_remote "$HOST1" "powertop --csv='$H1_test_dir$PATH_POWERTOP/powertop.csv' --sample=$time --time=$((time / 2)) --iteration=$((it / time)) &> /dev/null & " "$H1_pwrd"
    
    echo "Warmup period"
    sleep $warmup_time
    echo "Iniciando testes iperf..."
    t=3
    for i in $(seq 1 $n); do
        t=$((t + 1))
        b=$((i * 3))
        echo "Iniciando teste de Iperf numero: $i, BandWidth: $b'M'"
        run_remote "$HOST2" "ip netns exec $ue_namespace iperf -c $target_ip -P $p_clients -b $b'M' -t $i_time &> /dev/null " "$H2_pwrd"
        sleep $p_time
    done
    sleep 15
    echo "Reiniciando container do xApp no HOST2..."
    run_remote "$HOST2" "docker restart python_xapp_runner" "$H2_pwrd"
    echo "Aguardando turbostat e powertop terminarem..."
    run_remote "$HOST1" "while pgrep -x powertop > /dev/null; do sleep 1; done" "$H1_pwrd"
    run_remote "$HOST1" "while pgrep -x turbostat > /dev/null; do sleep 1; done" "$H1_pwrd"
    python3 csv_turbostat.py "$H1_test_dir/$PATH_TURBOSTAT" "$H1_test_dir/$PATH_RESULT_TS" "$WINDOW_SIZE" &
    python3 csv_powertop.py "$H1_test_dir$PATH_POWERTOP" "$H1_test_dir$PATH_RESULT_PT" "$WINDOW_SIZE"
    run_remote "$HOST1" "while pgrep -x csv_powertop.py > /dev/null; do sleep 1; done" "$H1_pwrd"
    echo "Processing the data at $(date)"
}

echo "Iperf server starting"
run_remote "$HOST2" "nohup docker exec -d $container_name iperf -s -p $port -e -i 1 --sum-only &> /dev/null " "$H2_pwrd"

# Itera sobre os modelos
for model in "${models[@]}"; do
    model_name="${model%.pkl}" 
    FOLDER_NAME="../${model_name}-${DATETIME}"
    mkdir -pv "$FOLDER_NAME"  &> /dev/null
    mkdir -pv "$FOLDER_NAME/$DIR_TURBOSTAT"  &> /dev/null
    mkdir -pv "$FOLDER_NAME/$DIR_POWERTOP/$DATETIME/"  &> /dev/null 
    mkdir -pv "$FOLDER_NAME/$DIR_RESULT_TS"  &> /dev/null
    mkdir -pv "$FOLDER_NAME/$DIR_RESULT_PT"  &> /dev/null

    FOLDER=$(basename "$FOLDER_NAME")

    PATH_TURBOSTAT="$FOLDER/$DIR_TURBOSTAT/turbostat-$DATETIME.csv"
    PATH_POWERTOP="$FOLDER/$DIR_POWERTOP/$DATETIME/"
    PATH_RESULT_TS="$FOLDER/$DIR_RESULT_TS/result_turbostat-$DATETIME.csv"
    PATH_RESULT_PT="$FOLDER/$DIR_RESULT_PT/result_powertop-$DATETIME.csv"

    echo "Iniciando xApp no HOST2 com o modelo: $model_name"
    if [ "$model" = "xgb_model.json" ]; then
        power_test &
        run_remote "$HOST2" "cd '$ric_sc_path' && nohup docker compose exec -T python_xapp_runner ./oranor_xapp_v6.5.py > /dev/null 2>&1 &" "$H2_pwrd" N 
    else    
        run_remote "$HOST2" "cd '$ric_sc_path' && nohup docker compose exec -T python_xapp_runner ./oranor_xapp_v6.py --buffer $X_BUFF --model /opt/xApps/models/$model > /dev/null 2>&1 &" "$H2_pwrd" N &
        power_test
    fi    
done
