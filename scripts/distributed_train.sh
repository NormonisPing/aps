#!/usr/bin/env bash

# Copyright 2019 Jian Wu
# License: Apache 2.0 (http://www.apache.org/licenses/LICENSE-2.0)

set -eu

gpu="0,1"
seed=777
distributed="torch"
epochs=100
init=""
resume=""
trainer="ddp"
tensorboard=false
batch_size=64
num_workers=8
eval_interval=-1
save_interval=-1
prog_interval=100
dev_batch_factor=1

echo "$0 $*"

. ./utils/parse_options.sh || exit 1

[ $# -ne 3 ] && echo "Script format error: $0 <task> <data-set> <exp-id>" && exit 1

task=$1
data=$2
exp_id=$3

opts=""
case $task in
  "am" | "lm" )
    dict=data/$data/dict
    [ ! -f $dict ] && echo "$0: missing dictionary $dict" && exit 1
    opts="--dict $dict"
    ;;
  "ss" )
    ;;
  * )
    echo "$0: Unknown task: $task" && exit 1
    ;;
esac

if [ "$task" = "lm" ]; then
  conf=conf/$data/nnlm/$exp_id.yaml
  checkpoint=exp/$data/nnlm/$exp_id
else
  conf=conf/$data/$exp_id.yaml
  checkpoint=exp/$data/$exp_id
fi

[ ! -f $conf ] && echo "$0: missing training configurations $conf" && exit 1

export OMP_NUM_THREADS=1

num_process=$(echo "print(len('$gpu'.split(',')))" | python)
echo "#num_process = $num_process, GPUs = $gpu"

case $distributed in
  "torch" )
    port=$(echo "import random; print(random.randint(10000, 20000))" | python)
    python -m torch.distributed.launch \
      --nnodes 1 \
      --nproc_per_node $num_process \
      --master_port $port \
      --use_env \
      cmd/train_$task.py $opts \
      --conf $conf \
      --seed $seed \
      --init "$init" \
      --resume "$resume" \
      --epochs $epochs \
      --trainer $trainer \
      --batch-size $batch_size \
      --device-ids $gpu \
      --checkpoint $checkpoint \
      --num-workers $num_workers \
      --distributed $distributed \
      --tensorboard $tensorboard \
      --save-interval $save_interval \
      --prog-interval $prog_interval \
      --eval-interval $eval_interval \
      --dev-batch-factor $dev_batch_factor \
      > $data.train_$task.$exp_id.log 2>&1
    ;;
  "horovod" )
    horovodrun -np $num_process \
      -H localhost:$num_process \
      cmd/train_$task.py $opts \
      --conf $conf \
      --seed $seed \
      --init "$init" \
      --resume "$resume" \
      --epochs $epochs \
      --trainer $trainer \
      --batch-size $batch_size \
      --device-ids $gpu \
      --checkpoint $checkpoint \
      --num-workers $num_workers \
      --distributed $distributed \
      --tensorboard $tensorboard \
      --save-interval $save_interval \
      --prog-interval $prog_interval \
      --eval-interval $eval_interval \
      --dev-batch-factor $dev_batch_factor \
      > $data.train_$task.$exp_id.log 2>&1
    ;;
  * )
    echo "$0: Unknown --distributed $distributed" && exit 1
    ;;
esac

cp $data.train_$task.$exp_id.log exp/$data/$exp_id
