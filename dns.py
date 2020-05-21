# -*- coding: utf-8 -*-
import wmi
import ctypes
import sys

arrDNSServers=['223.5.5.5', '114.114.114.114']
is_ask = False

def set_dns(objNicConfig):
    returnValue = objNicConfig.SetDNSServerSearchOrder(DNSServerSearchOrder = arrDNSServers)
    if returnValue[0] == 0 or returnValue[0] == 1:
        print('成功设置网卡DNS：', objNicConfig.Description)
    else:
        print(str(returnValue), '修改失败: DNS设置发生错误，网卡为', objNicConfig.Description)

def auto_set_dns():
    wmiService = wmi.WMI()
    colNicConfigs = wmiService.Win32_NetworkAdapterConfiguration(IPEnabled = True)
    if len(colNicConfigs) < 1:
        print('没有找到可用的网络适配器')
        exit()
    if is_ask:
        objNicConfig = colNicConfigs[0]
        if (len(colNicConfigs) > 1):
            print("-------------------------------------------------------\n")
            print("0(默认): 所有网卡")
            for i in range(len(colNicConfigs)):
                print(str(i+1)+" : ",colNicConfigs[i].IPAddress)
            print("-------------------------------------------------------\n")
            i=input("选择以太网卡：\n")
            i=int(i)
            objNicConfig = colNicConfigs[i-1]
        set_dns(objNicConfig)
    else:
        for objNicConfig in colNicConfigs:
            set_dns(objNicConfig)

'''
print "-----------------------------------------"
print objNicConfig.IPAddress
print objNicConfig.IPSubnet
print objNicConfig.DefaultIPGateway
print objNicConfig.DNSServerSearchOrder
print "-----------------------------------------"
'''

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
if is_admin():
    auto_set_dns()
else:
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

input("\n\n运行完成，此操作将DNS设置为淘宝与114开放的DNS服务，请放心使用。\n\n\n按回车键(Enter)退出。")