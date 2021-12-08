import socket               # Import socket module
from threading import *
import os
import glob
import sys
import platform
import datetime
import time

def handle_peers():
    print("handling Peers")
    client_peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_peer_host = socket.gethostbyname(host)
    client_peer_port = port
    client_peer_socket.bind((client_peer_host, client_peer_port))
    client_peer_socket.listen(5)

    while flag:
        (peer_socket, peer_addr) = client_peer_socket.accept()
        print('Got connection from', peer_addr)
        new_thread = Thread(target=peer_connection, args=(peer_socket,))
        new_thread.start()

    client_peer_socket.close()

def peer_connection(peer_socket):
    data = peer_socket.recv(1024).decode()
    print("peer request\n")
    print(data)
    first_line=data.split('\n')[0]
    first_line_arr=first_line.split()
    rfc=first_line_arr[2]

    file_lists=glob.glob('*.txt')
    response=""
    if not rfc.isdecimal():
        response=P2P_version + " " + "400 Bad Request\n"
        peer_socket.send(response.encode())
    else:
        for file in file_lists:
            if "RFC"+rfc+".txt" in file:
                f_size = os.path.getsize(file)
                get_mod_time=time.ctime(os.stat(file)[-2])
                response = P2P_version+" 200 OK\n" + "Date: " + str(datetime.datetime.now().strftime(
                    "%A, %d. %B %Y %I:%M%p")) + "\nOS: " + platform.system() + "\nLast-Modified: "+ get_mod_time+ "\nContent-Length: " + str(
                    f_size) + '\n' + "Content-Type: text/plain\n"
                peer_socket.send(response.encode("utf8"))
                with open(file, encoding="utf8") as f:
                    file_data = f.read(1024).encode("utf8")

                    while file_data:
                        peer_socket.send(file_data)
                        file_data = f.read(1024).encode("utf8")
                    f.close()
                break


    if len(response)==0:
        response=P2P_version + " " + "404 Not Found\n"
        peer_socket.send(response.encode())
    peer_socket.close()
    print("Enter an number corresponding to the function you want")
    print("1. Lookup RFC")
    print("2. List all RFC")
    print("3. Download an RFC file")
    print("4. Quit")

#to send requests to the central server_host
def send_requests(note):
    client_socket.send(note.encode())
    response = client_socket.recv(1024).decode()
    print('Central Server response :')
    print(response)


#to send download requests to other peers
def peer_requests(note, peer_host, peer_port,rfc):
    client_socket = socket.socket()
    try:
        client_socket.connect((peer_host, peer_port))
    except OSError:
        print("Address/port related error connecting to peer")
        return

    client_socket.send(note.encode())
    response = client_socket.recv(1024).decode()
    print('response from the peer :')
    data_list  = response.split('\n',6)


    if data_list[0].split()[1] == '200':
        file_data = data_list[6].encode("utf8")
        response = '\n'.join(data_list[:6])
        print(response)
        #print("Inside if")
        name = "RFC" + str(rfc) + ".txt"
        with open(name, 'wb') as f:
            f.write(file_data)
            while True:
                data = client_socket.recv(1024)

                if not data:
                    break
                f.write(data)
        f.close()
        add_rfc(rfc, "NA")
    else:
        print(response)
    client_socket.close()

#send a request to list all rfc's
def list_rfc():
    note = "LIST "+ P2P_version+"\nHost: "+host+'\n'+"Port: "+str(port)
    send_requests(note)

#accept input and send requests to add rfc's
def add_rfc( rfc, title):

    note = "ADD RFC " +str(rfc)+" "+P2P_version+"\nHost: "+host+'\n'+"Port: "+str(port)+'\n'+"Title: "+title
    send_requests(note)


#accept input and send requests to find a rfc
def lookup_rfc():
    print('Please enter a RFC number you want to look for ( ex: 1234)')
    rfc = str(input())
    print('Please enter the title of the mentioned RFC ( Case sensitive )')
    title = input()
    note = "LOOKUP RFC " +str(rfc)+" "+P2P_version+"\nHost: "+host+'\n'+"Port: "+str(port)+'\n'+"Title: "+title
    send_requests(note)

#download rfc from another peer
def download_rfc():
    print('Please enter the hostname of peer having the RFC')
    peer_host = input()
    print('Please enter the port number of peer having the RFC')
    int_flag=True
    while int_flag:
        try:
            peer_port = int(input())
            int_flag=False
        except ValueError:
            print("enter an integer value for port number ")

    print('Please enter the RFC you want')
    rfc = str(input())
    #title = 'rfc' + str(rfc)
    rfc_file_list = glob.glob('*.txt')
    for file in rfc_file_list:
        if "RFC"+str(rfc)+".txt" in file:
            print("File already exists")
            return
    note = "GET RFC " +str(rfc)+" "+P2P_version+"\nHost: "+host+'\nOS: '+ platform.system()
    peer_requests(note,peer_host, peer_port, rfc)



def server_requests():
    # for the first time a peer joins the system


    join_request = "JOIN "+P2P_version+"\nHost: " + host + '\n' + "Port: " + str(port)
    send_requests(join_request)

    #send_requests(note, server_host, server_port)
    rfc_file_list = glob.glob('*.txt')
    for file in rfc_file_list:
        if "_" in file:
            file_split=file.split("_")
            title = file_split[0]
            rfc = file_split[1].split('.')[0][3:]
            add_rfc(rfc,title)

    while (True):
        print("Enter an number corresponding to the function you want")
        print("1) Lookup RFC")
        print("2) List all RFC")
        print("3) Download an RFC file")
        print("4) Quit")
        option = str(input())
        if (option == '1'):
            lookup_rfc()
        elif (option == '2'):
            list_rfc()
        elif (option == '3'):
            download_rfc()
        elif (option == '4'):
            close_request = "CLOSE "+P2P_version+"\nHost: " + host + '\n' + "Port: " + str(port)
            flag=False
            send_requests(close_request)
            break
        else:
            print('please enter a valid choice')






server_flag=True
while server_flag:
    try:
        server_host = input("Enter the hostname of the central server: ")
        server_port = 7734
        client_socket = socket.socket()
        client_socket.connect((server_host, server_port))
        server_flag=False
    except OSError:
        print("Address/port related error connecting to peer. Enter a correct hostname")

P2P_version="P2P-CI/1.0"

flag=True
host = socket.gethostname()
port = 5678
peer_thread = Thread(target=handle_peers)
peer_thread.daemon = True
peer_thread.start()
server_requests()