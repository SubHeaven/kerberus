# -*- coding: utf-8 -*-
import codecs
import datetime
import json
import os
import psutil
import sys
import time

from subprocess import Popen, CREATE_NEW_CONSOLE

iacon_process_list = {}
services_list = []

def load_service_list():
    services_list = []
    if os.path.isfile("kerberus.json"):
        with codecs.open("kerberus.json", "r", "utf8") as file:
            services_list = json.loads(file.read())
    return services_list

def update_service_list(services_list):
    with codecs.open("kerberus.json", "w+", "utf8") as file:
        file.write(json.dumps(services_list, indent=4, ensure_ascii=False))

def need_to_restart(process, starting=False):
    result = process['restart'] or starting
    n = datetime.datetime.now()
    current_time = f"{str(n.hour).rjust(2,'0')}:{str(n.minute).rjust(2,'0')}:{str(n.second).rjust(2,'0')}"
    result = result and (process['startat'] == "" or process['startat'] <= current_time)
    result = result and (process['stopat'] == "" or process['stopat'] > current_time)
    return result

def checkservices(starting=False, services_list=[]):
    os.system("cls")
    n = datetime.datetime.now()
    current_time = f"{str(n.hour).rjust(2,'0')}:{str(n.minute).rjust(2,'0')}:{str(n.second).rjust(2,'0')}"
    print(current_time)
    print("╔═════════════════════════════════════════════╦══════════╦═══════════╦═══════════╦══════════════════════════════════════════════════════╗")
    print("║ Serviço                                     ║   PID    ║   CPU %   ║   RAM %   ║  Status                                              ║")
    print("╠═════════════════════════════════════════════╬══════════╬═══════════╬═══════════╬══════════════════════════════════════════════════════╣")
    for i in range(len(services_list)):
        is_running = psutil.pid_exists(services_list[i]['pid'])
        if (services_list[i]['pid'] == 0 or not is_running):
            if need_to_restart(services_list[i], starting):
                services_list[i] = runOnNewWindow(services_list[i])
                print(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║     0     ║     0     ║ STARTED                                              ║")
            else:
                print(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║     0     ║     0     ║ STOPPED (It Starts at {services_list[i]['startat']}) ║")
        elif is_running:
            if services_list[i]['stopat'] != "" and services_list[i]['stopat'] < current_time and services_list[i]['pid'] != 0:
                print(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║     0     ║     0     ║ STOPPING                                             ║")
                os.system(f"taskkill /PID {services_list[i]['pid']}")
                services_list[i]['status'] = "waiting"
            else:
                process = psutil.Process(services_list[i]['pid'])
                services_list[i]['cpu'] = round(process.cpu_percent(), 2)
                services_list[i]['ram'] = round(process.memory_percent(), 2)
                print(f"║ {services_list[i]['title'].ljust(44, ' ')}║ {str(services_list[i]['pid']).center(8,' ')} ║ {str(round(process.cpu_percent(), 2)).center(9,' ')} ║ {str(round(process.memory_percent(), 2)).center(9,' ')} ║ OK                                                   ║")

    print("╚═════════════════════════════════════════════╩══════════╩═══════════╩═══════════╩══════════════════════════════════════════════════════╝")

    return services_list

def runOnNewWindow(service):
    try:
        defaultdir = os.getcwd()
        os.chdir(service['path'])
        service['pid'] = Popen(service['command'], creationflags=CREATE_NEW_CONSOLE).pid
        service['status'] = "running"
        os.chdir(defaultdir)
    except Exception as exc:
        service['status'] = "stopped"
        print(exc)
    return service

def start_guardian():
    services_list = load_service_list()
    checkservices(starting=True, services_list=services_list)
    while True:
        services_list = checkservices(services_list=services_list)
        update_service_list(services_list)
        time.sleep(1)

def clearStringParam(param):
    if (param[0] == "'" and param[-1:] == "'") or (param[0] == "'" and param[-1:] == "'"):
        param = param[1:-1]
    return param

def printHelp():
    print("╔═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗")
    print("║ Processa o arquivo ECD indicado. Se o caminho for um diretório, classifica e processa todos os arquivos encontrados.                    ║")
    print("║    Se for marcado apenas para mapear, apenas lê, classifica os dados e mostra-os na tela para conferência com o                         ║")
    print("║    valor total.                                                                                                                         ║")
    print("║                                                                                                                                         ║")
    print("║ Parâmetros:                                                                                                                             ║")
    print("║     -empresa    = Informa a empresa da nota a ser processada                                                                            ║")
    print("║     -pack       = Opcional. Ao finalizar o processamento, cria uma cópia do resultado na pasta.                                         ║")
    print("║     -empacotar  = Idem acima.                                                                                                           ║")
    print("║     -foldered   = Gera os resumos para o Iacon nas pastas informadas.                                                                   ║")
    print("║     -filter     = Filtra as pastas processadas. Exemplo -filter=\"Novas%\" processaria apenas as pastas que iniciam com \"Novas\"           ║")
    print("║     -especial   = Aplica apenas a regra de nota existente na domínio.                                                                   ║")
    print("║ Forma de uso do script:                                                                                                                 ║")
    print("║     python nfe.py <Caminhos dos arquivos>                                                                                               ║")
    print("║                                                                                                                                         ║")
    print("║ Exemplo:                                                                                                                                ║")
    print("║     python nfe.py \"C:\\Spool\\30769960000181-52300040116-20180622-20181231-G-754575E6130FED2963F7DC9FD288BFADCA6AD94C-1-SPED-ECD.xml\"     ║")
    print("║ ou:                                                                                                                                     ║")
    print("║     python nfe.py \"S:\\\"                                                                                                                 ║")
    print("║ ou:                                                                                                                                     ║")
    print("║     python nfe.py \"S:\\\" -foldered                                                                                                       ║")
    print("║     python nfe.py \"S:\\\" -foldered -filter=\"C:\\Iacon XML\\466\"                                                                                                      ║")
    print("║                                                                                                                                         ║")
    print("╚═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    args = []
    vars = {}
    vars['command'] = sys.argv[0]
    vars['process'] = True
    vars['consolidar'] = False
    vars['help'] = False
    vars['path'] = ""
    vars['empresa'] = ""
    vars['mesini'] = 0
    vars['anoini'] = 0
    vars['mesfim'] = 0
    vars['anofim'] = 0
    for arg in sys.argv[1:]:
        parts = arg.split('=')
        if (len(parts) > 1):
            if parts[0] == 'caminho':
                vars['path'] = clearStringParam(parts[1])
            elif parts[0] == 'empresa':
                vars['empresa'] = clearStringParam(parts[1])
            elif parts[0] == 'mesini':
                vars['mesini'] = int(clearStringParam(parts[1]))
            elif parts[0] == 'anoini':
                vars['anoini'] = int(clearStringParam(parts[1]))
            elif parts[0] == 'mesfim':
                vars['mesfim'] = int(clearStringParam(parts[1]))
            elif parts[0] == 'anofim':
                vars['anofim'] = int(clearStringParam(parts[1]))
        else:
            args.append(parts[0])
            if (parts[0]  == "processar"):
                vars['consolidar'] = True
            elif (parts[0]  == "help" or parts[0]  == "ajuda"):
                vars['help'] = True
            elif (vars['path']  == ""):
                vars['path'] = parts[0]
    
    start_guardian()