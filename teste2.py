# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import psutil

def pid_exists(pid):
    for p in psutil.process_iter():
        if p.pid == pid:
            return True
    return False

print(pid_exists(5588))