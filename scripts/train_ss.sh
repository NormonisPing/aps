#!/usr/bin/env bash

# wujian@2019

set -eu

gpu=0
seed=777
epoches=100
tensorboard=false
batch_size=64
num_workers=4
eval_interval=-1
save_interval=-1
prog_interval=100

echo "$0 $@"

. ./utils/parse_options.sh || exit 1

[ $# -ne 2 ] && echo "Script format error: $0 <data-set> <exp-id>" && exit 1

data=$1
exp_id=$2
conf=conf/$data/$exp_id.yaml

[ ! -f $conf ] && echo "$0: missing training configurations $conf" && exit 1

src/train_ss.py \
  --conf $conf \
  --seed $seed \
  --tensorboard $tensorboard \
  --save-interval $save_interval \
  --prog-interval $prog_interval \
  --num-workers $num_workers \
  --checkpoint exp/$data/$exp_id \
  --batch-size $batch_size \
  --epoches $epoches \
  --device-id $gpu \
  --eval-interval $eval_interval \
  > $data.train_ss.$exp_id.log 2>&1

cp $data.train_ss.$exp_id.log exp/$data/$exp_id