import socket,sys
h=sys.argv[1]
s=socket.create_connection((h,5900),5); s.settimeout(5)
v=s.recv(12); print("server:",v.decode().strip())
s.sendall(b"RFB 003.008\n")
n=s.recv(1)
if n==b'\x00':
    ln=int.from_bytes(s.recv(1),'big'); print("handshake failed:",s.recv(ln).decode('latin1')); sys.exit()
cnt=n[0]; types=list(s.recv(cnt))
names={0:'Invalid',1:'None',2:'VNC-Auth',5:'RA2',6:'RA2ne',16:'Tight',18:'TLS',19:'VeNCrypt',30:'AppleARD'}
print("security types:",[(t,names.get(t,t)) for t in types])
