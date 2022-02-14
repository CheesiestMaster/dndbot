#!/bin/bash
while : ;do
echo "python start"
./bot.py
echo "python end"
sleep=$(head -1 ./recoverconf)
echo "sleep start $sleep"
sleep "$sleep"
done
