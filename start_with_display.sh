#!/bin/bash
sleep 5
export DISPLAY=:0
cd ~/raspi-ai-trashcan
source .venv/bin/activate
python -m src.smart_bin > ~/smartbin.log 2>&1 &

sleep 3
WID=$(xdotool search --name "Smart Recycling Bin" | head -1)
if [ -n "$WID" ]; then
  xdotool windowmove "$WID" 2560 0
  xdotool windowsize "$WID" 1024 600
fi
wait
