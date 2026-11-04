import socket

IP = ''
PORT = 443

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect(( IP, PORT))

while True:
    data = c.recv(1024).decode().strip()
    if data == '/exit':
        exit()
    else:
        print(data)