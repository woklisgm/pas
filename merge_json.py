#!/usr/bin/env python3
import json
import os

# перед запуском установить  pyjq 
# apt-get install autoconf automake build-essential libtool python-dev
# pip3 install pyjq 
import pyjq

# смотрим список файлов в директории где лежит сам скрипт
files = os.listdir()

# рекурсивыный проход словаря 
# это пока не надо, но возможно потом пригодится
def jq_recurse(json_data, search_field, list_for_data):
    if type(json_data) is dict and json_data:
        if search_field in json_data:
            list_for_data.append(json_data)
        for key in json_data:
            jq_recurse(json_data[key], search_field, list_for_data)

    elif type(json_data) is list and json_data:
        for entity in json_data:
            jq_recurse(entity, search_field, list_for_data)

# Определяем имена серверов файлы которых надо смерджить
def get_servernames_for_merge(files):
    hostnames = [file.split('.')[0] for file in files]
    for_merge = []
    for host in set(hostnames):
        if hostnames.count(host) > 1:
            for_merge.append(host)
    return for_merge  # список серверов файлы которых надо мерджить

def merge_json_files(hostname):
    # Открываем через менеджер контекста файл с основными данными
    with open('{}.json'.format(hostname), 'r') as json_file:
        main_data = json.load(json_file)
    # Тут открываем рейдконтроллеры
    with open('{}-raidcontroller.json'.format(hostname), 'r') as json_file:
        raidcontroller = json.load(json_file)
    # Тут диски из рейда
    with open('{}-raiddisk.json'.format(hostname), 'r') as json_file:
        raiddisk = json.load(json_file)
    # Добавляем данные из raiddisk Response Data в структуру json с контроллером
    raidcontroller['Disks'] = raiddisk.get('Controllers')[0].get('Response Data')
    # Затем добовляем ее в основной json 
    main_data['contraid'] = raidcontroller
    # пишем результат в файл вида hostname.json
    with open('{}.r.json'.format(hostname), 'w') as json_file:
        json_file.write(json.dumps(main_data,ensure_ascii=False, indent=4))


def parse_json_file(hostname):
	# файл с данными для парсинга
    with open('{}.r.json'.format(hostname), 'r') as json_file:
        main_data = json.load(json_file)

    # маска строки с последующим форматированием
        mask_string = '''{{"ComputerName":"{ComputerName}",
    "MachineType":"{MachineType}",
    "Manufacturer":"{Manufacturer}",
    "HWModel":"{HWModel}",
    "BiosSerialNumber":"{BiosSerialNumber}",
    "BaseBoardManufacturer":"{BaseBoardManufacturer}",
    "BaseBoardModel":"{BaseBoardModel}",
    "BaseBoardSerialNumber":"{BaseBoardSerialNumber}",
    "UUID":"{UUID}",
    "CpuName":"{CpuName}",      
    "CpuCount":"{CpuCount}",
    "CpuCores":"{CpuCores}",
    "CpuThreads":"{CpuThreads}",
    "CpuSpeed":"{CpuSpeed}",
    "OsName":"Linux",
    "OsCSDVersion":"n/a",
    "OsManufacturer":"n/a",
    "OsSerialNumber":"n/a",
    "OsVersion":"{OsVersion}",
    "NetAdapters":{NetAdapters},
    "NetInterfaces":{NetInterfaces},
    "MemoryInfo":{MemoryInfo},
    "Storage":{{
        "Contollers":{Contollers},
        "Drives":{Drives}
    }}}}'''.format(
        ComputerName = pyjq.one(".id", main_data),
        MachineType = pyjq.one(".configuration.family", main_data),
        Manufacturer = pyjq.one(".vendor", main_data),
        HWModel = pyjq.one(".product", main_data),
        BiosSerialNumber = pyjq.one(".serial", main_data),
        BaseBoardManufacturer = pyjq.first('.children[] | select(.id == "core") | .vendor', main_data),
        BaseBoardModel = pyjq.first('.children[] | select(.id == "core") | .product', main_data),
        BaseBoardSerialNumber = pyjq.first('.children[] | select(.id == "core") | .serial', main_data),
        UUID = pyjq.one(".configuration.uuid", main_data),
        CpuName = pyjq.first('recurse(.children[]?) | select(.class=="processor") | .product', main_data),
        CpuCount = pyjq.one('[recurse(.children[]?) | select((.class == "processor") and (.id | startswith("cpu:")))] | length', main_data),
        CpuCores = pyjq.first('recurse(.children[]?) | select(.class=="processor") | .configuration.cores', main_data),
        CpuThreads = pyjq.first('recurse(.children[]?) | select(.class=="processor") | .configuration.threads', main_data),
        CpuSpeed = pyjq.first('recurse(.children[]?) | select(.class=="processor") | (.size / 1000000)', main_data),
        OsVersion = pyjq.first('recurse(.children[]?) | select((.id == "network") and (.class == "network")) | .configuration.driverversion', main_data),
        NetAdapters = json.dumps(pyjq.all('''recurse(.children[]?) 
                                | select ((.id|startswith("network:")) and (.class == "network") and (.capabilities.ethernet == true)) 
                                | {MacAddress: .serial, AdapterName: .logicalname}''', main_data), ensure_ascii=False, indent=4),
        NetInterfaces = json.dumps(pyjq.all('''.children[]
                                | select (.class == "network")
                                | {Subnet: "n/a", IpAddress: .configuration.ip, InterfaceName: .logicalname, MacAddress: .serial}''', main_data), ensure_ascii=False, indent=4),
        MemoryInfo = json.dumps(pyjq.all('''recurse(.children[]?)
                                | select ((.class == "memory") and (.id|startswith("bank:")) and (.size != null))
                                | {Manufacturer: .vendor, Capacity: (.size / 1024 / 1024),
                                type: .description, PartNumber: .product, SerialNumber: .serial, Slot: .slot, speed: (.clock / 1000000)}''', main_data), ensure_ascii=False, indent=4),
        Contollers = json.dumps(pyjq.all('''recurse(.children[]?)
                                 | select (.class == "storage" and .capabilities.raid == true) | {Manufacturer: .vendor, Version: .product}''', main_data), ensure_ascii=False, indent=4),
        Drives = json.dumps(pyjq.all('''recurse(.children[]?)
                            | select ((.class == "disk") and (.id|startswith("disk:")) and ((.size != null) or (.capacity != null)))
                            | {vendor: .vendor, id: .physid, Size: ((.size / 1024 / 1024 / 1024)? // (.capacity / 1024 / 1024 / 1024) | floor),
                            SerialNumber: .serial, Model: .product}''', main_data), ensure_ascii=False, indent=4),
        )

        # print(json.dumps(pyjq.all('''recurse(.children[]?) 
        #                         | select ((.id|startswith("network:")) and (.class == "network") and (.capabilities.ethernet == true)) 
        #                         | {MacAddress: .serial, AdapterName: .logicalname}''', main_data), ensure_ascii=False, indent=4))

    # сперва преобразуем строку в json а потот записываем в файл чтобы правильно расставились все скобочки
    result = json.loads(mask_string)
    # файл для записи результата
    with open('{}.output'.format(hostname), 'w') as output_file:
        output_file.write(json.dumps(result, ensure_ascii=False, indent=4))

# В цикле мерджим файлы серваков у которых несколько json файлов
for server in get_servernames_for_merge(files):
    # print(server)
    merge_json_files(server)
    parse_json_file(server)





