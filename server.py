import collections
import socket
from threading import Thread
from multiprocessing import Lock


########################################################################################################################
client_list = collections.OrderedDict()
RFC_list = collections.OrderedDict()
lock=Lock()
########################################################################################################################
def join_client(host_name, port):
    client_list[host_name] = port
    message = P2P_version + " " + "200 OK\n"
    #client_socket.send(message.encode())
    return message

########################################################################################################################
def add_rfc(hostname, rfc_num, title, port):
    if rfc_num in RFC_list:
        if title=="NA":
            title=RFC_list[rfc_num][0][1]
        RFC_list[rfc_num].append([hostname, title])

    else:
        RFC_list[rfc_num] = [[hostname, title]]
    line1 = P2P_version + " " + "200 OK"
    line2 = "RFC" + " " + rfc_num + " " + title + " " + port
    response = line1 + "\n" + line2 + "\n"
    #client_socket.send(response.encode())
    return response

########################################################################################################################
def rfc_lookup(rfc_num, title):
    code = ""
    line2 = ""
    line1 = P2P_version + " "
    if not rfc_num.isdecimal():
        code="400 Bad Request"
    elif rfc_num not in RFC_list:
        code = "404 Not Found"
    else:
        for rfc in RFC_list[rfc_num]:
            if title == rfc[1]:
                line2 += "RFC " + rfc_num + " " + title + " " + rfc[0] + " " + client_list[rfc[0]] + "\n"
            else:
                code = "404 Not Found"

    if len(line2) > 0:
        code = "200 OK"

    response = line1 + code + "\n" + line2
    return response

########################################################################################################################
def list_all():

    line2=""
    if len(RFC_list)==0:
        response = P2P_version + " " + "404 Not Found\n"

    else:

        for rfc in RFC_list:
            for row in RFC_list[rfc]:
                line2+= "RFC " + rfc + " " + row[1] + " " + row[0] + " " + client_list[row[0]] + "\n"

        line1 = P2P_version + " " + "200 OK"
        response=line1+"\n"+line2

    return response

########################################################################################################################
def close_client(hostname):
    print("CLOSE")
    if hostname in client_list:
        print("host present")
        del client_list[hostname]
        for rfc in RFC_list:
            print(rfc)
            leng_list=len(RFC_list[rfc])
            i=0
            while i<leng_list:
                print(RFC_list[rfc][i][0],hostname)
                if RFC_list[rfc][i][0]==hostname:
                    RFC_list[rfc].remove(RFC_list[rfc][i])
                    leng_list-=1
                else:
                    i+=1
        response = P2P_version + " " + "200 OK\n"
    else:
        response=P2P_version + " " + "404 Not Found\n"
    print(RFC_list)
    return response



########################################################################################################################
def handle_request(client_socket):
    flag=True
    host_name=""
    while flag:
        get_len = 1024
        data = client_socket.recv(get_len)
        get_mssg = bytearray(data).decode().split("\n")
        first_line = get_mssg[0].split(" ")
        #print(first_line)

        if first_line[0] == "JOIN":
            if first_line[1] != P2P_version:
                response = first_line[1] + " " + "505 P2P-CI Version Not Supported"
                client_socket.send(response.encode())
            else:
                response=join_client(get_mssg[1].split()[1], get_mssg[2].split()[1])
                client_socket.send(response.encode())
        elif first_line[0]=="CLOSE":
            if first_line[1] != P2P_version:
                response = first_line[1] + " " + "505 P2P-CI Version Not Supported"
                client_socket.send(response.encode())
            else:
                flag = False
                lock.acquire()
                response=close_client(get_mssg[1].split()[1])
                lock.release()
                client_socket.send(response.encode())
                client_socket.close()


        else:
            if first_line[0] == "ADD":
                version = first_line[3]
                if version != P2P_version:
                    response = version + " " + "505 P2P-CI Version Not Supported"
                    client_socket.send(response.encode())
                else:
                    rfc_num = first_line[2]
                    hostname = get_mssg[1].split(" ")[1]
                    title = get_mssg[3].split(" ",1)[1]
                    port = get_mssg[2].split(" ")[1]
                    lock.acquire()
                    response=add_rfc(hostname, rfc_num, title, port)
                    lock.release()
                    client_socket.send(response.encode())

            elif first_line[0] == "LOOKUP":
                version = first_line[3]
                if version != P2P_version:
                    response = version + " " + "505 P2P-CI Version Not Supported"
                    client_socket.send(response.encode())
                else:
                    rfc_num = first_line[2]
                    # hostname = get_mssg[1].split(" ")[1]
                    title = get_mssg[3].split(" ")[1]
                    # port = get_mssg[2].split(" ")[1]
                    response=rfc_lookup(rfc_num, title)
                    client_socket.send(response.encode())

            elif first_line[0] == "LIST":
                version = first_line[1]
                if version != P2P_version:
                    response = version + " " + "505 P2P-CI Version Not Supported"
                    client_socket.send(response.encode())
                else:
                    response=list_all()
                    client_socket.send(response.encode())

########################################################################################################################
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host = socket.gethostbyname(socket.gethostname())
port = 7734
print("Server Hostname: ", socket.gethostname())
print("Server port: ",port)

server_socket.bind((server_host, port))
server_socket.listen(5)
P2P_version="P2P-CI/1.0"

while True:
    client_socket, address = server_socket.accept()
    print("client socket:", client_socket, "address", address)
    create_thread = Thread(target=handle_request, args=(client_socket,))
    create_thread.start()

server_socket.close()
