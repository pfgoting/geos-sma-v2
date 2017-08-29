from paramiko import SSHClient
from scp import SCPClient

host = '192.168.0.199'
user = 'root'
pw = 'kmi'
rockdir = '/data/events'

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.connect('example.com')

with SCPClient(ssh.get_transport()) as scp:
    scp.put('test.txt', 'test2.txt')
    scp.get('test2.txt')