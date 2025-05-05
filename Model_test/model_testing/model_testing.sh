echo "Script initialized at $(date)"

source model.conf
source script.conf
source ../../env/env.conf

DATETIME=$(date +%Y%m%d-%H%M%S)
mapfile -t models < <(ssh -o StrictHostKeyChecking=no "$HOST2" "ls -1 $model_dir")

run_remote() {
    local host="$1"
    local password="$2"
    local command="$3"

    ssh -o StrictHostKeyChecking=no "$host" "echo '$password' | sudo -S bash -c '$command'"

    if [ $? -ne 0 ]; then
        echo "Erro ao executar comando no host $host: $command"
        exit 1
    fi
}
for model in "${models[@]}"; do
    FOLDER_NAME="../$model-$DATETIME"
    mkdir -pv "$FOLDER_NAME"
    dur=$((n*i_time + n*p_time + warmup_time + 10))

    run_remote "$HOST2" "$H2_pwrd" "cd $ric_sc_path && nohup docker compose exec python_xapp_runner ./oranor_xapp_v6.py --model "/opt/xApps/models/$model" > /dev/null 2>&1 "  &
    run_remote "$HOST1" "$H1_pwrd" "$H1_model_testing_dir/power.sh $FOLDER_NAME"  &
    run_remote "$HOST2" "$H2_pwrd" "$H2_model_testing_dir/power.sh"

    sleep $dur
    run_remote "$HOST2"  "$H2_pwrd" "docker restart python_xapp_runner&&"
    sleep 5
done    