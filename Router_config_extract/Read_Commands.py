from netmiko import NetMikoTimeoutException, NetMikoAuthenticationException
from netmiko import ConnectHandler
import re,os
from datetime import datetime


class RouterAccess:

    def __init__(self):

        self.core_ip_list = RouterAccess.core_device_ip()  # 1st method to fetch this data
        self.credentials = RouterAccess.read_creds()
        self.file_path_list = self.cdp_ip_file_extract()  # This has extracted list of file names create a dict
        self.command_list = RouterAccess.read_commands()  # 2nd Method to get the command list
        self.cdp_ip_dict = self.cdp_neighbors_dict()  # this has extracted ip information from CDP neighbor

    @staticmethod
    def core_device_ip(file='Input/device_ip.txt'):
        """ Extract Core Switch IP address from the text file
            and return the list of core switch ips to connect"""
        device_ip_file = open(file, 'r')
        device_ip_line = device_ip_file.read()
        core_device_ip_list = device_ip_line.strip().splitlines()[1:]
        return core_device_ip_list # Core Device IP List

    @staticmethod
    def read_commands(file='./Input/commands.txt'):
        """This takes the commands from input commands file
            and returns the list of commands """
        with open(file, 'r') as f:
            cmd_list = f.read()
        return cmd_list.strip().splitlines()    # create a list of commands

    @staticmethod
    def read_creds(file='./Input/username_passwords.txt'):
        """This function takes the input from text file and converts
            user credentials in to list"""
        with open(file, 'r') as f:
            cred_list = f.read()
            creds_list = cred_list.strip().splitlines()[1:]
            return creds_list[0:3]    # Read creds file and create a list

    def cdp_ip_file_extract(self):

        file_list = []

        for core_ip in self.core_ip_list:
            core_device = {'ip': core_ip,
                            'username': self.credentials[0],
                            'password': self.credentials[1],
                            'secret': self.credentials[2],
                            'device_type': 'cisco_ios'}
            core_device_connect = ConnectHandler(**core_device)
            core_device_connect.enable()
            with open('./Output'+'//'+core_ip+'.txt','w') as file:
                core_cdp_data = core_device_connect.send_command_expect('show cdp nei det')
                file.write(core_cdp_data)
            core_device_connect.disconnect()
            file_list.append(str('./Output'+'//'+core_ip+'.txt'))
        return file_list

    def cdp_neighbors_dict(self):

        file_list = self.file_path_list
        device_name = re.compile(r'(?:Device ID:)\s(.+)')
        mgmt_add_search = re.compile(r'(Entry a.+)')
        mgmt_add = re.compile(r'(?:  IP address:) (\d+.\d+.\d+.\d+)')
        value = False
        final_dict = {}
        i = 0
        for file in file_list:
            fileopen = open(file)
            device_dict = {}
            for line in fileopen:
                if device_name.match(line):
                    device = device_name.match(line).group(1)
                    # print(device)
                if mgmt_add_search.match(line):
                    value = True
                if value == True and mgmt_add.search(line):
                    # print(mgmt_add.match(line).group(1))
                    device_dict[device] = mgmt_add.match(line).group(1)
                    value = False
            fileopen.close()
            final_dict[self.core_ip_list[i]] = device_dict
            i+=1
            os.remove('./' + file)
        return final_dict

    def final_device_config_gen(self):

        for core_ip in self.cdp_ip_dict.keys():
            start_time = datetime.now()
            print("connecting to core {}".format(core_ip))
            core_device = {'ip': core_ip,
                           'username': self.credentials[0],
                           'password': self.credentials[1],
                           'secret': self.credentials[2],
                           'device_type': 'cisco_ios'}
            core_net_connect=ConnectHandler(**core_device)
            core_net_connect.enable()
            core_net_connect.send_command('terminal leng 0')
            print("connected to : ", core_net_connect.find_prompt())
            core_folder = os.path.join('./Output',core_ip)
            if not os.path.isdir(core_folder):
                os.mkdir(core_folder)
            for device_commands in self.command_list:
                print("capturing command {} from {}".format(device_commands,core_ip))
                core_output = core_net_connect.send_command_expect(device_commands, delay_factor=3)
                with open(os.path.join(core_folder, core_ip + '.txt'), 'a+') as core_file:
                    core_file.write('\n\n'+device_commands+'\n\n')
                    core_file.write(core_output)
                    core_file.write('\n\n')
            print("Writing commands to text file completed")
            core_net_connect.disconnect()
            end_time = datetime.now()
            print("Total time {}".format(end_time-start_time))

            for hname, device_ip in self.cdp_ip_dict[core_ip].items():
                d_start_time = datetime.now()
                print("Connecting to sub device {}".format(device_ip))
                sub_device = {'ip': device_ip,
                              'username': self.credentials[0],
                              'password': self.credentials[1],
                              'secret': self.credentials[2],
                              'device_type': 'cisco_ios'}
                sub_device_net_connect = ConnectHandler(**sub_device)
                sub_device_net_connect.enable()
                sub_device_net_connect.send_command('terminal leng 0')
                print("connected to : ", sub_device_net_connect.find_prompt())
                for device_commands in self.command_list:
                    print("capturing command {} from {}".format(device_commands, device_ip))
                    device_output = sub_device_net_connect.send_command_expect(device_commands, delay_factor=3)
                    with open(os.path.join(core_folder, device_ip + '.txt'), 'a+') as device_file:
                        device_file.write('\n\n' + device_commands + '\n\n')
                        device_file.write(device_output)
                        device_file.write('\n\n')
                print("Writing commands to text file completed")
                sub_device_net_connect.disconnect()
                d_end_time = datetime.now()
                print("Total time {}".format(d_end_time - d_start_time))
        print("Data Capture Completed ")



    # def creds_2_dict_sets(self):
    #     """ Here the user credential list will be imported and
    #         generate credential dictionary sets"""
    #     creds = self.read_creds()
    #     cred_set_dict = {}
    #     j = 0
    #     k = 3
    #     for i in range(int(len(creds)/3)):
    #         cred_set_dict.update({'cred_set'+str(i) : creds[j:k]})
    #         j += 3
    #         k += 3
    #     return cred_set_dict  # Device Credentials set

    # @staticmethod
    # def creds_generation():
    #     """This will generate individual credentials
    #         extract from dictionary set"""
    #     username = dict_set[0]
    #     password = dict_set[1]
    #     secret = dict_set[2]
    #     return username, password, secret

    # def device_config_extract(self):
    #
    #     for device_ip in self.cdp_ip_list:
    #         device_data = {'ip' : device_ip,
    #                        'username' : device_creds_list[0],
    #                        'password' : device_creds_list[1]
    #                        'secret' : device_creds_list[2]
    #                        'device_type': 'cisco_ios'}
    #         net_connect = ConnectHandler(**device_data)
    #         net_connect.enable()
    #         for command in commands_list:
    #             device_command_output = net_connect.send_command_expect(command,delay_factor = 5)


    def print_output(self):
        # print(self.core_ip_list)
        # print(self.command_list)
        # print(self.credentials)
        # print(self.cdp_ip_dict)
        # print(self.file_path_list)
        self.final_device_config_gen()



    # def core_ssh_connection(self):
    #     """ This method is to connect to core switch and
    #         verify credentials, extract cdp neighbor data"""
    #     flag = False
    #     cred_set = self.creds_2_dict_sets()
    #     core_ip_list = self.core_device_ip()
    #     for ip_add in core_ip_list:
    #         ip = ip_add
    #         for i in range(len(cred_set)):
    #             dict_set = cred_set['cred_set'+str(i)]
    #             username, password, secret = self.creds_generation(dict_set)
    #             core_device = {'ip':ip,
    #                            'username':username,
    #                            'password':password,
    #                            'secret':secret,
    #                            'device_type':'cisco_ios'}
    #             try:
    #                 print("Connecting IP {}".format(ip))
    #                 net_connect = ConnectHandler(**core_device)
    #                 net_connect.enable()
    #                 core_hostname = net_connect.send_command_expect('show runn | in hostname')
    #                 print(core_hostname)
    #                 flag = True
    #                 if flag:
    #                     break
    #
    #             except NetMikoTimeoutException:
    #                 print("Connection Time out, ensure device is reachable")
    #                 break
    #             except NetMikoAuthenticationException:
    #                 print("Invalid Credentials, Trying next set of user names and passwords")







ra = RouterAccess()
command_list = ra.print_output()






