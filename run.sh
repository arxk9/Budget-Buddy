#!/bin/bash
source /web/projects/hackybot/venv/bin/activate
gunicorn server:app -b 127.0.0.1:$PORT -w=4
