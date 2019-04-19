<<<<<<< HEAD
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
        self.core_hostname = re.compile(r'(?:hostname\s)(\w+\S\w+.+)')
        self.total_device_dict = {}

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
            print("Executing show commands on {}".format(ip))
            for command in self.device_commands():
                dev_command = net_connect.send_command_timing(command,delay_factor=2)
                # print("executing: {} on {} ".format(command,ip))
                with open(os.path.join(folder, ip+'.txt'), 'a+') as file:
                    file.write('\n' + net_connect.find_prompt() + " " + command + '\n')
                    file.write(dev_command)
                    file.write('\n')
            net_connect.disconnect()
            print(ip + " Written Successfully under output folder with file name as {} ".format(ip+'.txt'))
        except NetmikoTimeoutError:
            print(ip + " Please ensure Device is accessible, Not able to Connect")
        except NetmikoAuthError:
            print(ip + " user Creds are wrong, please verify login manually")
        except ValueError:
            print("Some issue connecting {} device please try again".format(ip))

    def core_hostname_extract(self, core_device_ip):
        core_device = {'ip': core_device_ip,
                       'username': self.uname,
                       'password': self.passwd,
                       'device_type': 'cisco_ios',
                       'secret': self.secret}
        core_device_hostname = ""
        try:
            core_connect = ConnectHandler(**core_device)
            core_connect.enable()
            core_runn = core_connect.send_command_expect("show runn | in hostname")
            core_connect.disconnect()
            for line in core_runn.splitlines():
                if self.core_hostname.match(line):
                    core_device_hostname = self.core_hostname.match(line).group(1)

        except NetmikoTimeoutError:
            print(core_device_ip + " Device not accessible")
            return None
        except NetmikoAuthError:
            print(core_device_ip + " Credentials are wrong")
            return None

        return core_device_hostname

    def device_cdp_extract(self, core_device_ip):

        dev_ip = core_device_ip
        neighbor_ip_list = []
        device_name_list = []
        device_name = ""
        flag = False
        core_device_name = self.core_hostname_extract(core_device_ip)

        if core_device_name is not None:
            device_name_list.append(core_device_name)
            neighbor_ip_list.append(dev_ip)
            i = 1
            print("Connecting to {}, to execute show commands".format(dev_ip))
            print("Network discovery in progress... ")
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
                        elif self.mgmt_entry_search.match(line):
                            flag = True
                        elif flag and self.mgmt_ip_add.match(line):
                            dist_device_ip = self.mgmt_ip_add.match(line).group(1)
                            if dist_device_ip not in neighbor_ip_list and device_name not in device_name_list:
                                device_name_list.append(device_name)
                                neighbor_ip_list.append(dist_device_ip)
                                flag = False
                    dev_ip = neighbor_ip_list[i]
                    i += 1
                except IndexError:
                    print("Network Discovery Completed")
                    print("Device List in given site : ", neighbor_ip_list)
                    break
                except NetmikoTimeoutError:
                    print(dev_ip + " Not able to Connect, Please ensure Device is accessible")
                except NetmikoAuthError:
                    print(dev_ip + " user Creds are wrong, please verify login manually")
            return neighbor_ip_list
        else:
            return None

    def config_extract_final(self):

        for core_ip in self.device_list:
            str_time = datetime.now()
            print("Access core switch {} from input File ".format(core_ip))
            ip_list = self.device_cdp_extract(core_ip)
            self.total_device_dict[core_ip] = ip_list
            if ip_list is not None:
                print("*" * 80)
                for device_ip in ip_list:
                    self.device_config_extract('site'+'-'+core_ip, device_ip)
                end_time = datetime.now()
                print("Time Taken to complete complete site from Core is {}".format(end_time - str_time))
            else:
                print("*"*80)
                print("Checking for next available device if any")
                print("*" * 80)

        print("Project Completed")
        print(self.total_device_dict)


if __name__ == "__main__":
    sc = ShowCommands()
    sc.config_extract_final()
