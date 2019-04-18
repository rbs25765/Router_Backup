from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutError
from netmiko import NetmikoAuthError
from datetime import datetime
import os
import re


class ShowCommands:

    def __init__(self):

        self.input_device_ip_file = r'./Input/device_ip.txt'
        self.input_show_commands_file = r'./Input/commands.txt'
        self.creds_file = r'./Input/username_passwords.txt'

        self.device_list = self.core_device_extract()
        self.user_creds = self.device_creds()

        self.uname = self.user_creds[0]
        self.passwd = self.user_creds[1]
        self.secret = self.user_creds[2]

        self.device_name = re.compile(r'(?:Device ID:)\s(.+)')
        self.mgmt_entry_search = re.compile(r'(Entry a.+)')
        self.mgmt_ip_add = re.compile(r'(?:  IP address:) (\d+.\d+.\d+.\d+)')

    def core_device_extract(self):
        with open(self.input_device_ip_file, 'r') as file:
            file = file.read()
            device_list = file.strip().splitlines()[1:]
        return device_list

    def device_commands(self):
        with open(self.input_show_commands_file, 'r') as file:
            device_commands = file.read()
            command_list = device_commands.strip().splitlines()[1:]
        return command_list

    def device_creds(self):
        with open(self.creds_file, 'r') as file:
            user_creds = file.read()
            user_creds = user_creds.strip().splitlines()[1:]
        return user_creds

    def device_config_extract(self, core_folder, ip, device_type='cisco_ios'):
        device = {'ip':ip,
                  'username': self.uname,
                  'password': self.passwd,
                  'device_type': device_type,
                  'secret': self.secret}
        try:
            folder = os.path.join('./Output', core_folder)
            if not os.path.exists(folder):
                os.makedirs(folder)
            net_connect = ConnectHandler(**device)
            net_connect.enable()
            for command in self.device_commands():
                print("Executing show commands on {}".format(ip))
                dev_command = net_connect.send_command_timing(command,delay_factor=2)
                # print("executing: {} on {} ".format(command,ip))
                with open(os.path.join(folder, ip+'.txt'), 'a+') as file:
                    file.write('\n' + net_connect.find_prompt() + " " + command + '\n')
                    file.write(dev_command)
                    file.write('\n')
            net_connect.disconnect()
            print(ip + " Written Successfully under output folder with file name as {} ".format(ip+'.txt'))
        except NetmikoTimeoutError:
            print("Please ensure Device is accessible, Not able to Connect")
        except NetmikoAuthError:
            print(ip + " user Creds are wrong, please verify login manually")
        except ValueError:
            print("Some issue connecting {} device please try again".format(ip))

    def device_cdp_extract(self, core_device_ip):

        dev_ip = core_device_ip
        core_device_neighbor_list = []
        device_name_list = []
        flag = False
        core_device_neighbor_list.append(dev_ip)
        i = 1
        print("Executing Commands and Writing files, please be patient")
        while True:
            core_device = {'ip': dev_ip,
                           'username': self.uname,
                           'password': self.passwd,
                           'device_type': 'cisco_ios',
                           'secret': self.secret}
            try:
                core_connect = ConnectHandler(**core_device)
                core_connect.enable()
                cdp_out = core_connect.send_command_expect("show cdp neighbor detail")
                for line in cdp_out.splitlines():
                    if self.device_name.match(line):
                        device_name = self.device_name.match(line).group(1)
                    if self.mgmt_entry_search.match(line):
                        flag = True
                    if flag and self.mgmt_ip_add.match(line):
                        dist_device_ip = self.mgmt_ip_add.match(line).group(1)
                        if dist_device_ip not in core_device_neighbor_list and device_name not in device_name_list:
                            device_name_list.append(device_name)
                            core_device_neighbor_list.append(dist_device_ip)
                            flag = False
                dev_ip = core_device_neighbor_list[i]
                i += 1
            except IndexError:
                print("Network Discovery Completed")
                print("Device List in given site : ", core_device_neighbor_list)
                break
            except NetmikoTimeoutError:
                print(dev_ip + " Not able to Connect, Please ensure Device is accessible")
                break
            except NetmikoAuthError:
                print(dev_ip + " user Creds are wrong, please verify login manually")
                break
        return core_device_neighbor_list

    def config_extract_final(self):
        for core_ip in self.device_list:
            str_time = datetime.now()
            print("Access {} from input File ".format(core_ip))
            ip_list = self.device_cdp_extract(core_ip)
            for device_ip in ip_list:
                self.device_config_extract('site'+'-'+core_ip, device_ip)
            end_time = datetime.now()
            print("Time Taken to complete complete site from Core is {}".format(end_time - str_time))
        print("Project Completed")


if __name__ == "__main__":
    sc = ShowCommands()
    sc.config_extract_final()
