import socket,struct,sys
h=sys.argv[1]; out=sys.argv[2]
s=socket.create_connection((h,5900),5); s.settimeout(10)
assert s.recv(12).startswith(b"RFB")
s.sendall(b"RFB 003.008\n")
cnt=s.recv(1)[0]; types=list(s.recv(cnt))
s.sendall(bytes([1]))                      # choose None auth
r=struct.unpack(">I",s.recv(4))[0]; assert r==0,("securityresult",r)
s.sendall(b"\x01")                         # ClientInit shared
hdr=s.recv(24)
w,h2=struct.unpack(">HH",hdr[:4])
bpp,depth,be,tc=hdr[4],hdr[5],hdr[6],hdr[7]
rmax,gmax,bmax=struct.unpack(">HHH",hdr[8:14])
rsh,gsh,bsh=hdr[14],hdr[15],hdr[16]
nl=struct.unpack(">I",hdr[20:24])[0]; name=s.recv(nl).decode('latin1')
print(f"name={name!r} size={w}x{h2} bpp={bpp} depth={depth} big_endian={be} truecolor={tc} rgbmax=({rmax},{gmax},{bmax}) shift=({rsh},{gsh},{bsh})")
# force 32bpp truecolor BGRA, little-endian
s.sendall(struct.pack(">Bxxx BBBB HHH BBB xxx",0,32,24,0,1,255,255,255,16,8,0))
s.sendall(struct.pack(">BxH I",2,1,0))     # SetEncodings: Raw(0) only
s.sendall(struct.pack(">BBHHHH",3,0,0,0,w,h2))  # FBUpdateRequest full
def rd(n):
    b=b""
    while len(b)<n:
        c=s.recv(n-len(b));
        if not c: raise EOFError
        b+=c
    return b
assert rd(1)[0]==0; rd(1)
nrect=struct.unpack(">H",rd(2))[0]
import zlib
buf=bytearray(w*h2*4)
for _ in range(nrect):
    x,y,rw,rh,enc=struct.unpack(">HHHHi",rd(12))
    assert enc==0,("enc",enc)
    data=rd(rw*rh*4)
    for row in range(rh):
        src=row*rw*4
        dst=((y+row)*w+x)*4
        buf[dst:dst+rw*4]=data[src:src+rw*4]
# write PPM (RGB) from BGRA
with open(out,"wb") as f:
    f.write(b"P6\n%d %d\n255\n"%(w,h2))
    px=bytearray(w*h2*3)
    for i in range(w*h2):
        px[i*3]=buf[i*4+2]; px[i*3+1]=buf[i*4+1]; px[i*3+2]=buf[i*4]
    f.write(px)
print("wrote",out)
