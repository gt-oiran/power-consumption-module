#!/bin/bash
source env.conf

# Função para executar comandos remotos com sudo
run_remote() {
    local host="$1"
    local command="$2"
    local password="$3"

    ssh -o StrictHostKeyChecking=no "$host" "echo '$password' | sudo -S bash -c '$command'"

    if [ $? -ne 0 ]; then
        echo "Erro ao executar comando no host $host: $command"
        exit 1
    fi
}

# Encerra o srsUE no HOST2
run_remote "$HOST2" "pkill srsue" "$H2_pwrd"

# Encerra todos os contêineres Docker no HOST2
run_remote "$HOST2" "docker kill \$(docker ps -q)"

# Encerra o gNB no HOST1
run_remote "$HOST1" "pkill gnb" "$H1_pwrd"

echo "Ambiente encerrado"