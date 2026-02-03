#!/bin/bash
# Script de rulare Flask cu gunicorn
cd /home/ubuntu/csh-predict/backend
gunicorn -w 2 -b 0.0.0.0:5005 --timeout 300 --keep-alive 5 app:app
