#!/bin/bash
source env.conf

# Função para executar comandos remotos com sudo
run_remote() {
    local host="$1"
    local password="$3"
    local command="$2"

    # Verifica se o comando é para criar um namespace
    if [[ "$command" == *"ip netns add"* ]]; then
        local namespace=$(echo "$command" | awk '{print $4}')  # Extrai o nome do namespace
        ssh -o StrictHostKeyChecking=no "$host" "
            if ip netns list | grep -q '$namespace'; then
                echo 'O namespace $namespace já existe. Ignorando criação.'
            else
                sudo $command
            fi
        "
    # Verifica se o comando é para adicionar uma rota
    elif [[ "$command" == *"ip route add"* ]]; then
        local route=$(echo "$command" | awk '{print $4, $5, $6}')  # Extrai a rota
        ssh -o StrictHostKeyChecking=no "$host" "
            if ! ip route show | grep -q '$route'; then
                sudo $command
            else
                echo 'A rota $route já existe. Ignorando adição.'
            fi
        "
    else
        ssh -o StrictHostKeyChecking=no "$host" "echo '$password' | sudo -S bash -c '$command'"
    fi

    if [ $? -ne 0 ]; then
        echo "Erro ao executar comando no host $host: $command"
        exit 1
    fi
}

run_remote "$HOST2" "ip netns add $ue_ns"
run_remote "$HOST1" "ip route add $open5gs_docker_addr via $HOST2_ip"
run_remote "$HOST2" "cd $srs_5gc && nohup docker compose up --build 5gc > /tmp/open5gs.log 2>&1 &" &
echo "Open5GS está sendo executado."
sleep 5

run_remote "$HOST2" "cd $ric_sc_path && nohup docker compose up  > /tmp/oran-ric-sc.log 2>&1 &" &
echo "ORAN-RIC-SC está sendo executado."
sleep 15 

run_remote "$HOST1"  "nohup $srs_gnb_path/gnb -c $srs_gnb_path/$gnb_yaml > /tmp/srsran_gnb.log 2>&1 & disown"
echo "srsRAN gNB está sendo executado." "$H1_pwrd"
sleep 5

run_remote "$HOST2" "nohup $srs_ue_path/srsue $srs_ue_path/$srs_ue > /dev/null 2>&1 & disown" "$H2_pwrd"
echo "srsRAN_UE esta sendo executado"
echo "Ambiente em execução"