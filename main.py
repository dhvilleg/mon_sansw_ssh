import paramiko
import ftplib
from paramiko.auth_handler import AuthenticationException, SSHException
import logging
import re
import datetime
from encriptor import key_create, key_write, file_decrypt, key_load, file_encrypt

class RemoteClient:
    def __init__(self, ipaddr, username, password):
        self.ipaddr = ipaddr
        self.username = username
        self.password = password
        self.client = None
        self.conn = None

    def connection(self):
        if self.conn is None:
            try:
                self.client = paramiko.SSHClient()
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(
                    self.ipaddr,
                    username=self.username,
                    password=self.password,
                    look_for_keys=False
                )
            except AuthenticationException as error:
                logging.error("autenticacion fallida, vuelva a intentar \n error es {}".format(error))
                raise error
        return self.client

    def disconnect(self):
        if self.client:
            self.client.close()

    def execute_unix_commands(self, command):
        self.conn = self.connection()
        stdin, stdout, stderr = self.conn.exec_command(command)
        stdout.channel.recv_exit_status()
        response = stdout.readlines()
        return response

    def reformat_list_into_table(self, switch_name, datetime, output_list):
        _count = 0
        _count_slot_port_avg = 0
        list = output_list
        header1 = []
        header2 = []
        header3 = []
        list_port_slot = []
        list_port_average = []
        list_join_slot_average = []

        for i in list:
            if re.search("\t", i):
                aux = i.replace('\t', "")
                aux = aux.replace('\n', "")
                aux = aux.replace('Total', "")
                aux = re.sub(r'  *', ' ', aux)
                header1.append(aux.split(' ')[1:17])
            if re.search("slot ", i):
                aux = i.replace('slot ', "")
                header2.append(aux.split(":")[0])
            if re.search("slot", i):
                aux = i.replace('slot ', "")
                aux = aux.replace('\n', "")
                aux = re.sub(r'.: *', '', aux)
                aux = re.sub(r'  *', ' ', aux)
                header3.append(aux.split(" ")[0:16])
        for i in header3:
            for e in i:
                if 'k' in e or 'm' in e:
                    list_port_average.append("{};{}".format(e[:-1], e[-1:]))
                else:
                    list_port_average.append("{};b".format(e))
        for i in header2:
            for e in header1:
                for j in e:
                    list_port_slot.append("{}/{}".format(i, j))
                    _count += 1
                if _count == 16:
                    _count = 0
                    del header1[0]
                    break
        for i in list_port_slot:
            for e in list_port_average:
                list_join_slot_average.append("{};{};{};{}".format(datetime, switch_name, i, e))
                _count_slot_port_avg += 1
                if _count_slot_port_avg == 1:
                    _count_slot_port_avg = 0
                    del list_port_average[0]
                    break
        return list_join_slot_average

    def create_report_file(self, switch_name, output_list):
        today = datetime.datetime.now()
        date_time = today.strftime("%Y-%m-%d %H:%M:%S")
        date = today.strftime("%Y-%m-%d")
        f = open("perf_{}{}.txt".format(switch_name, date), "w+")
        for i in self.reformat_list_into_table(switch_name, date_time, output_list):
            f.write("{}\n".format(i))
        f.close()
        return "perf_{}{}.txt".format(switch_name, date)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    output_list = []
    sansw_list = []
    ftp_list = []
    loaded_key = key_load('mykey.key')
    sansw_file = file_decrypt(loaded_key, 'sansw.conf', 'sansw.conf')
    ftp_file = file_decrypt(loaded_key, 'ftp_credentials.conf', 'ftp_credentials.conf')
    ftp_file = ftp_file.replace('\n', '')
    ftp_list = ftp_file.split(';')
    for i in sansw_file.split('\n'):
        if i != '':
            sansw_list.append(i.split(';'))
    for i in sansw_list:
        sansw_name = i[0]
        user = i[1]
        passwd = i[2]
        ip_addr = i[3]
        remote = RemoteClient(ip_addr, user, passwd)
        remote.connection()
        output_list = remote.execute_unix_commands("portperfshow -t 0")
        remote.disconnect()
        file_name_report = remote.create_report_file(sansw_name, output_list)
        ftp = ftplib.FTP(ftp_list[0], ftp_list[1], ftp_list[2])
        ftp.encoding = "utf-8"
        ftp.cwd("path/to/your/ftp/directory")
        ftp.storbinary('STOR '+file_name_report, open(file_name_report, 'rb'))
        ftp.close()
