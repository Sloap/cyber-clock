#!/bin/bash

cd /home/yoan/cyber-clock || exit 1

source .venv/bin/activate

python collector/main.py
python summarizer/main.py
python storer/main.py
python mailer/main.py
