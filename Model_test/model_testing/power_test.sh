#!/bin/bash
source script.conf
source ../../env/env.conf

it=$((n*i_time + n*p_time + warmup_time))
#Verificação de arquivos
echo "Verificando diretorios"
for dir in "$iperf_dir"; do
    if [ ! -d $dir ]; then
        mkdir -pv "$dir"
    fi
done

echo "Teste,Data,Hora,Resultado" > "$output_file"

#Inicio do server Iperf
echo "Iperf server starting"
docker exec -d $container_name iperf -s -p $port -e -i 1  --sum-only 


#warmup
echo "Warmup period" 
sleep $warmup_time

#Loop de testes Iperf
t=3
for i in $(seq 1 $n) ; do
    t=$((t + 1)) 
    b=$((i*5)) 
    echo "Iniciando teste de Iperf numero: $i , BandWidth: $b M"
    echo "Teste $i - $(date +%Y%m%d-%H%M%S)" >> "$output_file"
    echo $PASSWORD |sudo -S ip netns exec $ue_namespace iperf -c $target_ip -P $p_clients -b $b'M' -t $i_time >> "$output_file"
    sleep $p_time 
done 

#Finaliza execução 
# kill $vmstat_pid
echo "testes concluídos."
