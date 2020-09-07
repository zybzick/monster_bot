#!/bin/sh
echo !!!!! update and upgrade apt
sudo apt update -y
sudo apt upgrade -y
sudo apt install htop -y
sudo apt install tmux -y

echo !!!!! install git
sudo apt install git -y

echo !!!!! git clone
rm -rf MargoBot
git clone https://github.com/ueberkonfa/MargoBot.git

echo !!!!! install venv
sudo apt install python3.8-venv -y
python3 -m venv MargoBot/venv
. MargoBot/venv/bin/activate
python3 -m pip install --upgrade pip

echo !!!!!  install requiremenrs
pip3 install -r MargoBot/requirements.txt

echo !!!!! start
#tmux new-session -s margobot
#tmux attach -t margobot
#tmux kill-server
#MargoBot/venv/bin/python MargoBot/main.py
# ssh ueberkonfaadmin@130.193.38.106