# -*- coding: utf-8 -*-
import atexit
import argparse
import codecs
import datetime
import json
import os
import pickledb
import psutil
import shutil
import signal
import sys
import time
import uuid

from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image, ImageDraw

from bson import ObjectId
from pymongo import MongoClient
from subprocess import Popen, CREATE_NEW_CONSOLE, CREATE_NO_WINDOW

iacon_process_list = {}
services_list = []
current_pid = os.getpid()

def load_service_list():
    services_list = []
    if os.path.isfile("kerberus.json"):
        with codecs.open("kerberus.json", "r", "utf8") as file:
            services_list = json.loads(file.read())
    return services_list

def update_service_list(services_list):
    kerberus_services = MongoClient()['iacon']['kerberus_services']
    for service in services_list:
        if 'mongo' in service and kerberus_services.count_documents({"_id": ObjectId(service['mongo'])}, limit = 1) > 0:
            kerberus_services.update_one({"_id": ObjectId(service['mongo'])}, {"$set": service})
        else:
            kerberus_services.insert_one(service)
            service['mongo'] = str(service['_id'])
            del service['_id']
    with codecs.open("kerberus.json", "w+", "utf8") as file:
        file.write(json.dumps(services_list, indent=4, ensure_ascii=False))

def need_to_restart(process, starting=False, services_start=[]):
    if "local_stop" in process and process["local_stop"]:
        if process['uuid'] in services_start:
            process["local_stop"] = False
            return True
        else:
            return False
    else:
        result = process['restart'] or starting
        n = datetime.datetime.now()
        current_time = f"{str(n.hour).rjust(2,'0')}:{str(n.minute).rjust(2,'0')}:{str(n.second).rjust(2,'0')}"
        result = result and (process['startat'] == "" or process['startat'] <= current_time)
        result = result and (process['stopat'] == "" or process['stopat'] > current_time)
        return result

def ylog(msg):
    print(msg)

def nlog(msg):
    pass

def noconsolelog(msg, noconsole):
    if noconsole:
        ylog(msg)

def pid_exists(pid):
    for p in psutil.process_iter():
        if p.pid == pid:
            return True
    return False

def process_need_to_stop(service, list):
    now = datetime.datetime.now()
    current_time = f"{str(now.hour).rjust(2,'0')}:{str(now.minute).rjust(2,'0')}:{str(now.second).rjust(2,'0')}"
    if service['stopat'] != "" and service['stopat'] < current_time and service['pid'] != 0:
        return True
    else:
        if service['uuid'] in list:
            service['local_stop'] = True
            return True
    return False

def load_services_to_stop():
    pickle = pickledb.load('pickle.db', True)
    services_stop = pickle.lgetall('stop_service')
    pickle.lremlist('stop_service')
    return services_stop

def load_services_to_start():
    pickle = pickledb.load('pickle.db', True)
    services_stop = pickle.lgetall('start_service')
    pickle.lremlist('start_service')
    return services_stop

count = 0
def checkservices(starting=False, services_list=[], noconsole=False):
    global count

    if need_to_debug():
        ylog(912/0)

    if need_to_stop_kerberus():
        do_stop_kerberus(services_list)
        return

    if noconsole:
        llog = nlog
    else:
        os.system("cls")
        llog = ylog

    services_stop = load_services_to_stop()
    services_start = load_services_to_start()

    n = datetime.datetime.now()
    current_time = f"{str(n.hour).rjust(2,'0')}:{str(n.minute).rjust(2,'0')}:{str(n.second).rjust(2,'0')}"
    report_request = check_report_request()
    list_requested = check_list_request()
    requested_report = []
    requested_list = []
    llog(current_time)
    llog("╔═════════════════════════════════════════════╦══════════╦═══════════╦═══════════╦══════════════════════════════════════════════════════╗")
    if report_request:
        requested_report.append(" Serviço                                      -   PID    -   CPU %   -   RAM %   -  Status        - UUID")
    llog("║ Serviço                                     ║   PID    ║   CPU %   ║   RAM %   ║  Status                                              ║")
    llog("╠═════════════════════════════════════════════╬══════════╬═══════════╬═══════════╬══════════════════════════════════════════════════════╣")
    for i in range(len(services_list)):
        if not 'uuid' in services_list[i] or services_list[i]['uuid'] == "":
            services_list[i]['uuid'] = uuid.uuid4().hex

        is_running = pid_exists(services_list[i]['pid'])
        if list_requested:
            requested_list.append(f"{i} - {services_list[i]['name']} - {services_list[i]['title']}")

        active = "active" not in services_list[i] or services_list[i]["active"]

        if active and (services_list[i]['pid'] == 0 or not is_running):
            if report_request:
                requested_report.append(f" {services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} -     0     -     0     - stopped        - {services_list[i]['uuid']}")

            if need_to_restart(services_list[i], starting=starting, services_start=services_start):
                noconsolelog(f"{services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} is stopped. starting it.", noconsole)
                services_list[i] = runOnNewWindow(services_list[i])
                llog(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║     0     ║     0     ║ STARTED                                              ║")
                noconsolelog(f"{services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} started", noconsole)
                count += 1
                # if count > 0:
                #     sys.exit(8)
            else:
                llog(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║     0     ║     0     ║ STOPPED (It Starts at {services_list[i]['startat']}) ║")
        elif is_running:
            if process_need_to_stop(services_list[i], services_stop):
                if report_request:
                    requested_report.append(f" {services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} - {str(round(process.cpu_percent(interval=1), 2)).center(9,' ')} - {str(round(process.memory_percent(), 2)).center(9,' ')} - running        - {services_list[i]['uuid']}")

                llog(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║     0     ║     0     ║ STOPPING                                             ║")
                os.system(f"taskkill /PID {services_list[i]['pid']} /F")
                services_list[i]['status'] = "waiting"
                noconsolelog(f"{services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} is stopping", noconsole)
            else:
                process = psutil.Process(services_list[i]['pid'])
                if report_request:
                    requested_report.append(f" {services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} - {str(round(process.cpu_percent(), 2)).center(9,' ')} - {str(round(process.memory_percent(), 2)).center(9,' ')} - running        - {services_list[i]['uuid']}")

                services_list[i]['cpu'] = round(process.cpu_percent(), 2)
                services_list[i]['ram'] = round(process.memory_percent(), 2)
                llog(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║ {str(round(process.cpu_percent(), 2)).center(9,' ')} ║ {str(round(process.memory_percent(), 2)).center(9,' ')} ║ OK                                                   ║")
                # noconsolelog(f"{services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} is running", noconsole)

    llog("╚═════════════════════════════════════════════╩══════════╩═══════════╩═══════════╩══════════════════════════════════════════════════════╝")
    if report_request:
        save_report(requested_report)
    if list_requested:
        save_list(requested_list)

    return services_list

def runOnNewWindow(service):
    try:
        defaultdir = os.getcwd()
        os.chdir(service['path'])
        if "silent" in service and service["silent"]:
            flag = CREATE_NO_WINDOW
        else:
            flag = CREATE_NEW_CONSOLE
        pop = Popen(service['command'], creationflags=flag)
        service['pid'] = pop.pid
        service['status'] = "running"
        os.chdir(defaultdir)
    except Exception as exc:
        service['status'] = "stopped"
        ylog(exc)
    return service

def start_guardian(noconsole=False, dieon=0):
    os.system("title=Kerberus - Monitoramento de Serviços")
    count = 0
    remove_pid()
    ylog(f"PID: {current_pid}")
    create_pid(current_pid)
    services_list = load_service_list()
    checkservices(starting=True, services_list=services_list, noconsole=noconsole)
    while True:
        services_list = checkservices(services_list=services_list, noconsole=noconsole)
        update_service_list(services_list)
        time.sleep(1)
        count += 1
        if dieon > 0 and count > dieon or need_to_stop():
            ylog("Saindo do kerberus...")
            for service in services_list:
                ylog(f"    Parando {service['pid']}")
                os.system(f"taskkill /PID {service['pid']} /F")
            sys.exit(1)

def get_pid():
    if os.path.isfile("kerberus.pid"):
        with codecs.open("kerberus.pid", "rb", "latin1") as file:
            expected_pid = file.read().strip()
            if expected_pid != "":
                return int(expected_pid)
    return 0

def check_guardian():
    expected_pid = get_pid()
    if expected_pid != 0:
        try:
            p = psutil.Process(expected_pid)
            # memoryUsed = p.memory_info()[0]/2.**30
            # print(f"RAM {memoryUsed} CPU {p.cpu_percent()}%")
            return True
        except psutil.NoSuchProcess as ex:
            ylog(ex)
            return False
        except psutil.AccessDenied as ex:
            ylog(ex)
            return False
        except psutil.ZombieProcess as ex:
            ylog(ex)
            return False
        except Exception as ex:
            ylog(ex)
            return False
    else:
        pass
    return False

def stop_guardian(clear = True):
    if check_guardian():
        pid = get_pid()
        with codecs.open(f"{pid}.st", "w+", "utf8") as file:
            file.write("true" if clear else "false")
        if clear:
            for service in services_list:
                os.system(f"taskkill /PID {service['pid']} /F")
        os.kill(pid, signal.SIGTERM)

def request_to_stop_kerberus():
    if check_guardian():
        pickle = pickledb.load('pickle.db', True)
        pickle.set('stop_kerberus', True)

def need_to_stop_kerberus():
    pickle = pickledb.load('pickle.db', True)
    if pickle.get('stop_kerberus'):
        pickle.rem('stop_kerberus')
        return True
    else:
        return False

def do_stop_kerberus(services_list):
    for service in services_list:
        os.system(f"taskkill /PID {service['pid']} /F")
    os.kill(get_pid(), signal.SIGTERM)

def stop_daemon(clear = True):
    if check_guardian():
        pickle = pickledb.load('pickle.db', True)
        pickle.set('stop_daemon', True)

def create_daemon(clear = True):
    if check_guardian():
        ylog("O kerberus já está rodando.")
    else:
        comm = f"pythonw3 {os.path.dirname(__file__)}\\kerberus.py -daemon".split(" ")
        pop = Popen(comm, creationflags=CREATE_NEW_CONSOLE)
        ylog(F" Daemon do kerberus rodando no PID {pop.pid}")

def request_debug():
    if check_guardian():
        pickle = pickledb.load('pickle.db', True)
        pickle.set('debug', True)

def need_to_debug():
    pickle = pickledb.load('pickle.db', True)
    if pickle.get('debug'):
        pickle.rem('debug')
        return True
    else:
        return False

def request_start_service(code):
    pickle = pickledb.load('pickle.db', True)
    pickle.ladd('start_service', code)

def request_stop_service(code):
    pickle = pickledb.load('pickle.db', True)
    pickle.ladd('stop_service', code)

def request_restart_service(code):
    pickle = pickledb.load('pickle.db', True)
    pickle.ladd('restart_service', code)

def need_to_start_service():
    pickle = pickledb.load('pickle.db', True)
    return pickle.llen('start_service') > 0

def need_to_stop_service():
    pickle = pickledb.load('pickle.db', True)
    return pickle.llen('stop_service') > 0

def need_to_restart_service():
    pickle = pickledb.load('pickle.db', True)
    return pickle.llen('restart_service') > 0

def need_to_start_service():
    pickle = pickledb.load('pickle.db', True)
    return pickle.llen('start_service') > 0

def need_to_stop_daemon():
    pickle = pickledb.load('pickle.db', True)
    if pickle.get('stop_daemon'):
        pickle.rem('stop_daemon')
        return True
    else:
        return False

def do_stop_daemon():
    ylog("Enviando comando para o Kerberus parar")
    # stop_guardian(clear=True)
    request_to_stop_kerberus()
    ylog("Parando o daemon")
    sys.exit(1)

def need_to_stop():
    filename = f"{current_pid}.st"
    if os.path.isfile(filename):
        os.remove(filename)
        return True
    else:
        return False

def check_report_request():
    filename = f"{current_pid}.rr"
    if os.path.isfile(filename):
        os.remove(filename)
        return True
    else:
        return False

def check_list_request():
    filename = f"{current_pid}.lr"
    if os.path.isfile(filename):
        os.remove(filename)
        return True
    else:
        return False

def request_report():
    if check_guardian():
        with codecs.open(f"{get_pid()}.rr", "w+", "utf8") as file:
            file.write("true")
        while not os.path.isfile(f"{get_pid()}.rrr"):
            time.sleep(1)
        report = ""
        with codecs.open(f"{get_pid()}.rrr", "r", "utf8") as file:
            report = file.read()
        os.remove(f"{get_pid()}.rrr")
        ylog(report)

def request_list():
    if check_guardian():
        with codecs.open(f"{get_pid()}.lr", "w+", "utf8") as file:
            file.write("true")
        while not os.path.isfile(f"{get_pid()}.lrr"):
            time.sleep(1)
        report = ""
        with codecs.open(f"{get_pid()}.lrr", "r", "utf8") as file:
            report = file.read()
        os.remove(f"{get_pid()}.lrr")
        ylog(report)

def save_report(requested_report):
    with codecs.open(f"{current_pid}.rrr", "w+", "utf8") as file:
        file.write("\n".join(requested_report))

def save_list(requested_list):
    with codecs.open(f"{current_pid}.lrr", "w+", "utf8") as file:
        file.write("\n".join(requested_list))

def show_status():
    load_service_list()
    for i in range(len(services_list)):
        is_running = pid_exists(services_list[i]['pid'])
        if (services_list[i]['pid'] == 0 or not is_running):
            ylog(f"{services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} is stopped.")
        elif is_running:
            ylog(f"{services_list[i]['title'].ljust(44, ' ')} - {str(services_list[i]['pid']).center(8,' ')} - {str(round(process.cpu_percent(), 2)).center(9,' ')} - {str(round(process.memory_percent(), 2)).center(9,' ')} - OK")

def remove_pid():
    if os.path.isfile("kerberus.pid"):
        os.remove("kerberus.pid")

def create_pid(new_pid):
    with codecs.open("kerberus.pid", "w+", "utf8") as file:
        file.write(str(new_pid))

def check_kerberus():
    pid = get_pid()
    is_running = pid > 0 and pid_exists(pid)
    if not is_running:
        comm = f"pythonw3 {os.path.dirname(__file__)}\\kerberus.py -noconsole".split(" ")
        pop = Popen(comm)
        ylog("Kerberus iniciado")
        return True
    else:
        return True
    return False

def start_daemon():
    while not need_to_stop_daemon():
        check_kerberus()
        time.sleep(2)
    do_stop_daemon()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Inicializa o guardião de serviços do Iacon', usage="python3 %(prog)s [options]")
    parser.add_argument('-noconsole', action="store_true", help='Não printa na tela o painel de status dos serviços')
    parser.add_argument('-check', action="store_true", help='Confere se o kerberus está rodando e, se sim, mostra o seu PID')
    parser.add_argument('-start', action="store_true", help='Inicializa o modo daemon do Kerberus')
    parser.add_argument('-stop', action="store_true", help='Finaliza o modo daemon do Kerberus')
    parser.add_argument('-status', action="store_true", help='Mostra na tela os status dos serviços configurados')
    parser.add_argument('-list', action="store_true", help='Mostra na tela a lista de serviços configurados')
    parser.add_argument('-daemon', action="store_true", help='Inicializa a versão do kerberus que vigia o kerberus')
    parser.add_argument('-dieon', type=int, default=0, help='contador de iteração para o sistema se desligar sozinho')
    parser.add_argument('-stop_service', type=str, help='Para a execução de um serviço')
    parser.add_argument('-start_service', type=str, help='Inicia a execução de um serviço')
    parser.add_argument('-restart_service', type=str, help='Reinicia a execução de um serviço')
    parser.add_argument('-debug', action="store_true", help='Causa algum efeito surpresa definido pelo SubHeaven enquanto faz testes')
    args = parser.parse_args()
    delete_pid_on_exit = False

    @atexit.register
    def onExit():
        if delete_pid_on_exit and os.path.isfile("kerberus.pid"):
            os.remove("kerberus.pid")

    if args.check:
        ylog(check_guardian())
    elif args.start_service:
        request_start_service(args.start_service)
    elif args.stop_service:
        request_stop_service(args.stop_service)
    elif args.restart_service:
        request_restart_service(args.restart_service)
    elif args.debug:
        request_debug()
    elif args.stop:
        # request_to_stop_kerberus()
        stop_daemon()
    elif args.start:
        create_daemon()
    elif args.status:
        request_report()
    elif args.list:
        request_list()
    elif args.daemon:
        start_daemon()
    else:
        delete_pid_on_exit = True
        start_guardian(noconsole = args.noconsole, dieon = args.dieon)