from netmiko import ConnectHandler
from netmiko import BaseConnection
from netmiko import Netmiko
import re,os
from datetime import datetime


def proxy_connect(file='output.txt'):
    
    net_connect = BaseConnection(
        device_type='cisco_ios',       
        ip='192.168.2.131', 
        username='cisco', 
        password='cisco', 
        secret='cisco'
        )
    net_connect.enable()
    cdp_neighbor = net_connect.send_command('show cdp neig det')
    file = open (file,'w+')
    file.write(cdp_neighbor)
    file.close()
    
  
def cdp_neighbors(file='output.txt'):
    
    device_name = re.compile(r'(?:Device ID:)\s(.+)')
    mgmt_add_search = re.compile(r'(Entry a.+)')
    mgmt_add = re.compile(r'(?:  IP address:) (\d+.\d+.\d+.\d+)')
    device_dict = {}
    value = False
    fileopen = open(file)
    for line in fileopen:
        if device_name.match(line):
            device = device_name.match(line).group(1)
        if mgmt_add_search.match(line):
            value = True
        if value == True and mgmt_add.search(line):
            device_dict[device]=mgmt_add.match(line).group(1)
            value = False
    fileopen.close()
    os.remove('./'+file)
    
    return device_dict



# def config_output():
#
#     proxy_device = proxy_connect()
#     out_dict = cdp_neighbors()
#     for hname,ip in out_dict.items():
#         start_time = datetime.now()
#         device = {'device_type':'cisco_ios',
#                 'ip':ip,
#                 'username':'cisco',
#                 'password':'cisco',
#                 'secret':'cisco'
#                   }
#         print("Connecting to {}".format(ip))
#         net_connect = ConnectHandler(**device)
#         net_connect.enable()
#         net_connect.send_command('term len 0')
#         print('Show running of {}'.format(ip))
#         run_output = net_connect.send_command_timing('show runn',delay_factor=5)
#         ip_int = net_connect.send_command_timing('show ip inter brief',delay_factor=8)
#         ip_inventory = net_connect.send_command_timing('show inventory',delay_factor=8)
#         with open('./Output'+'//'+ip+'-'+hname'.txt','w') as file:
#             file.write("Show Running Configuration \n")
#             file.write(run_output)
#             file.write("Show Ip Interface Brief \n")
#             file.write(ip_int)
#             file.write("Show inventory \n")
#             file.write(ip_inventory)
#         end_time = datetime.now()
#         net_connect.disconnect()
#         print("Total time taken to complete {:s}".format(str(end_time-start_time)))

config_output()

   
