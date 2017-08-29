import paramiko
from scp import SCPClient
import os, time
import threading
from threading import Thread

fpath = os.path.dirname(os.path.realpath(__file__))
port = 22
user = 'root'
pw = 'kmi'
rockdir = '/mnt/data1/data/events'
usrdir = os.path.join(os.path.split(fpath)[0],'rawData')

# ssh = SSHClient()
# ssh.load_system_host_keys()
# ssh.connect(host)

# with SCPClient(ssh.get_transport()) as scp:
#     scp.put('test.txt', 'test2.txt')
#     scp.get('test2.txt')

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def main1():
	host = '192.168.1.11'
	ssh = createSSHClient(host, port, user, pw)
	scp = SCPClient(ssh.get_transport())
	sftp = ssh.open_sftp()
	sftp.chdir(rockdir)
	dir_items = sftp.listdir()
	usrdir_items = os.listdir(usrdir)

	for item in dir_items:
		if not item in usrdir_items and '.evt' in item:
			print item
			# get files
			scp.get(rockdir+'/'+item,os.path.join(usrdir,item))

def main2():
	host = '192.168.1.22'
	ssh = createSSHClient(host, port, user, pw)
	scp = SCPClient(ssh.get_transport())
	sftp = ssh.open_sftp()
	sftp.chdir(rockdir)
	dir_items = sftp.listdir()
	usrdir_items = os.listdir(usrdir)

	for item in dir_items:
		if not item in usrdir_items and '.evt' in item:
			print item
			# get files
			scp.get(rockdir+'/'+item,os.path.join(usrdir,item))

def main3():
	host = '192.168.1.33'
	ssh = createSSHClient(host, port, user, pw)
	scp = SCPClient(ssh.get_transport())
	sftp = ssh.open_sftp()
	sftp.chdir(rockdir)
	dir_items = sftp.listdir()
	usrdir_items = os.listdir(usrdir)

	for item in dir_items:
		if not item in usrdir_items and '.evt' in item:
			print item
			# get files
			scp.get(rockdir+'/'+item,os.path.join(usrdir,item))

if __name__ == '__main__':
	while True:
		try:
			Thread(target = main1).start()
			# Thread(target = main2).start()
			# Thread(target = main3).start()
		except Exception as e:
			print e
			pass
		else:
			time.sleep(15)
		
		print "Done"