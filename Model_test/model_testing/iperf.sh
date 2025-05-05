#!/bin/bash
source script.conf
it=$((n*i_time + n*p_time + warmup_time))
#Verificação de arquivos
echo "Verificando diretorios"
for dir in "$DIRECTORY" "$vm_dir" "$vm_result" "$iperf_dir"; do
    if [ ! -d $dir ]; then
        mkdir -pv "$dir"
    fi
done

# #Cabeçalhos VMstat e powerTOP
# echo "r,b,swpd,free,buff,cache,si,so,bi,bo,in,cs,us,sy,id,wa,st,timestamp" > "$vm_csv"
# echo "Teste,Data,Hora,Resultado" > "$output_file"

# gnome-terminal -- bash -c "docker compose exec python_xapp_runner ./oranor_xapp_v4.py;exec bash"

#Inicio do vmstat e criação dos logs
echo "collecting vmstat metrics"
nohup vmstat -nwt 1 >> $vm_log &
vmstat_pid=$!

#Inicio do server Iperf
echo "Iperf server starting"
docker exec -d $container_name iperf -s -p $port -e -i 1  --sum-only 

# #Inicio powertop
# echo $PASSWORD | sudo -S powertop --csv="$(pwd)/$DIRECTORY/powertop.csv" --time=$time --iteration=$it  &> /dev/null  &
# powertop_pid=$! 
# trap "echo 'Encerrando powertop'; sudo kill $powertop_pid; kill $vmstat_pid; exit" SIGINT

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
    echo $PASSWORD |sudo -S ip netns exec $ue_namespace iperf -c $target_ip -P $p_clients -b $b'M' -i 1 -t $i_time >> "$output_file"
    sleep $p_time 
done 

# #Chamada de filtro Powertop
# python3 csv_pt.py $(pwd)/$DIRECTORY
#Construção do vmstat.csv 
awk 'NR > 2 {print $1","$2","$3","$4","$5","$6","$7","$8","$9","$10","$11","$12","$13","$14","$15","$16","$17","$18$19}' $vm_log >> "$vm_csv"

#Finaliza execução 
echo "Closing Iperf server"
docker exec $container_name bash -c 'kill $(pidof iperf)'
kill $vmstat_pid
#echo $PASSWORD | sudo -S kill $powertop_pid
echo "testes concluídos."
