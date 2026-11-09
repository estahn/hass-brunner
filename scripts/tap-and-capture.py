import socket,struct,sys,time
h=sys.argv[1]; out=sys.argv[2]
cx=int(sys.argv[3]) if len(sys.argv)>3 else None
cy=int(sys.argv[4]) if len(sys.argv)>4 else None
s=socket.create_connection((h,5900),5); s.settimeout(10)
assert s.recv(12).startswith(b"RFB"); s.sendall(b"RFB 003.008\n")
cnt=s.recv(1)[0]; list(s.recv(cnt)); s.sendall(bytes([1]))
assert struct.unpack(">I",s.recv(4))[0]==0
s.sendall(b"\x01"); hdr=s.recv(24)
w,H=struct.unpack(">HH",hdr[:4])
nl=struct.unpack(">I",hdr[20:24])[0]; s.recv(nl)
s.sendall(struct.pack(">Bxxx BBBB HHH BBB xxx",0,32,24,0,1,255,255,255,16,8,0))
s.sendall(struct.pack(">BxH I",2,1,0))
def rd(n):
    b=b""
    while len(b)<n:
        c=s.recv(n-len(b)); b+=c
    return b
if cx is not None:
    s.sendall(struct.pack(">BBHH",5,1,cx,cy)); time.sleep(0.05)  # button down
    s.sendall(struct.pack(">BBHH",5,0,cx,cy)); time.sleep(1.2)  # up
s.sendall(struct.pack(">BBHHHH",3,0,0,0,w,H))
assert rd(1)[0]==0; rd(1); nrect=struct.unpack(">H",rd(2))[0]
buf=bytearray(w*H*4)
for _ in range(nrect):
    x,y,rw,rh,enc=struct.unpack(">HHHHi",rd(12)); data=rd(rw*rh*4)
    for row in range(rh):
        d=((y+row)*w+x)*4; sidx=row*rw*4; buf[d:d+rw*4]=data[sidx:sidx+rw*4]
with open(out,"wb") as f:
    f.write(b"P6\n%d %d\n255\n"%(w,H))
    px=bytearray(w*H*3)
    for i in range(w*H): px[i*3]=buf[i*4+2];px[i*3+1]=buf[i*4+1];px[i*3+2]=buf[i*4]
    f.write(px)
print("ok",w,H)
