from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutError
from netmiko import NetmikoAuthError


class ShowCommands:

    def __init__(self):

        self.input_device_ip_file = r'./Input/device_ip.txt'
        self.input_show_commands_file = r'./Input/commands.txt'
        self.creds_file = r'./Input/username_passwords.txt'
        self.device_list = []
        self.command_list = []
        self.user_creds = []
        self.file_list = []
        self.router_dict = []
        self.value = []

    def core_device_extract(self):
        with open(self.input_device_ip_file, 'r') as file:
            file = file.read()
            self.device_list = file.strip().splitlines()[1:]
        return self.device_list

    def device_commands(self):
        with open(self.input_show_commands_file, 'r') as file:
            device_commands = file.read()
            self.command_list = device_commands.strip().splitlines()[1:]
        return self.command_list

    def device_creds(self):
        with open(self.creds_file, 'r') as file:
            user_creds = file.read()
            self.user_creds = user_creds.strip().splitlines()[1:]
        return self.user_creds

    def device_connect(self, ip, uname, passwd, secret, device_type='cisco_ios'):
        device = {  'ip':ip,
                    'username':uname,
                    'password':passwd,
                    'device_type':device_type,
                    'secret':secret}
        try:
            net_connect = ConnectHandler(**device)
            net_connect.enable()
            for command in self.device_commands():
                dev_command = net_connect.send_command_timing(command)
                with open ('./Output'+ip+'.txt', a+) as file:
                    file.write('\n' + command + '\n')
                    file.write(dev_command)
                    file.write('\n')
            net_connect.disconnect()
        except NetmikoTimeoutError:
            print("Please ensure Device is accessible, Not able to Connect directly")
        except NetmikoAuthError:
            print(ip + " user Creds are wrong, please verify login manually")








    def print_device(self):
        print(self.core_device_extract())
        print(self.device_commands())
        self.device_connect('192.168.1.1', 'cisco', 'cisco', 'cisco')




if __name__ == "__main__":
    sc = ShowCommands()
    sc.print_device()
