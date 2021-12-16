#! /bin/bash -eux

pip3 install -r requirements.txt --user
black main.py
isort main.py
