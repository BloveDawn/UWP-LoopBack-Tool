from winreg import *
from os import popen
from sys import argv
from getopt import getopt, GetoptError
from enum import Enum, auto


class GLOBAL:
    REG_ROOT_STR = HKEY_CURRENT_USER
    REG_PATH_STR = 'SOFTWARE\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppContainer\Mappings'

class COMMAND:
    EXECUTE = 'CheckNetIsolation.exe loopbackexempt'
    SHOW_LIST_PARAM = ' -s'
    ADD_PARAM = ' -a'
    DEL_PARAM = '-d'
    SID_PARAM = ' -p='

class PROCESS_MODE(Enum):
    REG_APP = auto()
    UNREG_APP = auto()


def RenameApp(app_name_ori_in:str) -> str:
    app_name = app_name_ori_in
    if '@' in app_name:
        app_name = app_name.split('_')[0].split('{')[1].replace('.', ' ')
    if '_' in app_name:
        app_name = app_name.replace('_', ' ')
    return app_name

def GetAppsNameAndSID(key_handle_in) -> dict:
    apps_dict = {}
    apps_count = QueryInfoKey(key_handle_in)[0]
    for app_index in range(apps_count):
        app_sid = EnumKey(key_handle_in, app_index)
        app_key_handle = OpenKey(key_handle_in, app_sid)
        if not app_key_handle:
            print('[-] AppSID ' + app_sid + ' invalid, please check it!')
            continue
        app_name = RenameApp(EnumValue(app_key_handle, 0)[1])
        apps_dict[app_name] = app_sid
        CloseKey(app_key_handle)
    return apps_dict

def ProcessSpecificApp(app_sid_in:str, process_mode:int) -> bool:
    if process_mode == PROCESS_MODE.REG_APP:
        command_excute_str = COMMAND.EXECUTE + COMMAND.ADD_PARAM + COMMAND.SID_PARAM + app_sid_in
    elif process_mode == PROCESS_MODE.UNREG_APP:
        command_excute_str = COMMAND.EXECUTE + COMMAND.DEL_PARAM + COMMAND.SID_PARAM + app_sid_in
    command_return_str = popen(command_excute_str).read()
    if '完成' in command_return_str or 'OK' in command_return_str:
        return True
    else:
        return False

def ShowAppsList():
    command_excute_str = COMMAND.EXECUTE + COMMAND.SHOW_LIST_PARAM
    command_return_str = popen(command_excute_str).read()
    print(command_return_str)

def ProcessAllApps(apps_dict_in:dict, process_mode_in:PROCESS_MODE):
    app_count = 0
    false_count = 0
    true_count = 0
    for app_name, app_sid in apps_dict_in.items():
        app_count += 1
        regist_result_flag = ProcessSpecificApp(app_sid, process_mode_in)
        print('['+ str(regist_result_flag) + ']-' + str(app_count) + '-AppName: ' + app_name + ', AppSid: ' + app_sid)
        if regist_result_flag:
            true_count += 1
        else:
            false_count += 1
    return true_count, false_count


if __name__ == '__main__':
    # init
    apps_list = []
    print('UWP apps loopback/proxy processor By blovedawn')
    print('[!] Warning: you must need admin priviledge to run this!')
    print('[!] Opening regkey')
    key_handle = OpenKey(key=GLOBAL.REG_ROOT_STR, sub_key=GLOBAL.REG_PATH_STR)
    print('[!] Getting apps...')
    apps_dict = GetAppsNameAndSID(key_handle)
    CloseKey(key_handle)
    
    # default option
    if(len(argv) == 1):
        print('[!] Run default option...(Add all apps to loopback list)')
        success_count, failed_count = ProcessAllApps(apps_dict, PROCESS_MODE.REG_APP)
        print('[!] Statistic:\n[+] Success count:' + str(success_count) + '\n[-] Fliled count:' + str(failed_count))
        pass

    # get opt
    try:
        opts, args = getopt(argv[1:], 'hadl',  ["help", "add_all", 'delete_all', 'special_add', 'special_delete'])
    except GetoptError:
        print('[!] Usage:')
        print('[!] UWPLoopBack [-a] [-d] [-l] [-h]')
        print('[!] Show help info: UWPLoopBack -h')
        exit(2)
    for opt, arg in opts:
        if opt == '-a':
            success_count, failed_count = ProcessAllApps(apps_dict, PROCESS_MODE.REG_APP)
            print('[!] Statistic:\n[+] Success count:' + str(success_count) + '\n[-] Fliled count:' + str(failed_count))
        elif opt == '-d':
            success_count, failed_count = ProcessAllApps(apps_dict, PROCESS_MODE.UNREG_APP)
            print('\n[!] Statistic:\n[+] Success count:' + str(success_count) + '\n[-] Fliled count:' + str(failed_count))
        elif opt == '-l':
            ShowAppsList()
        elif opt == '-h':
            print('[!] Help info:')
            print('[!] UWPLoopBack [-a] [-d] [-l] [-h]')
            print('[!] UWPLoopBack -a : Add all apps to Loopback list.')
            print('[!] UWPLoopBack -d : Delete all apps to Loopback list.')
            print('[!] UWPLoopBack -l : Show Loopback list.')
        else:
            print('[-] command line param error, please input [UWPLoopBack -h] get help.')
    input()