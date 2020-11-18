# -*- coding: utf-8 -*-
import os
import sys
import time

count = 0
while True:
    print("Oi")
    time.sleep(1)
    count += 1
    if count > 20:
        quit()