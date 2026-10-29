import struct, sys, collections

def parse(path):
    d = open(path, 'rb').read()
    p = 0
    secs = {}
    while p + 8 <= len(d):
        tag = d[p:p+4].decode('latin1'); ln = struct.unpack('<I', d[p+4:p+8])[0]
        secs[tag] = (p + 8, ln)
        p += 8 + ln
    return d, secs

def didx(d, secs):
    if 'DIDX' not in secs: return []
    o, ln = secs['DIDX']
    return [struct.unpack('<III', d[o+i:o+i+12]) for i in range(0, ln, 12)]

def hirc(d, secs):
    o, ln = secs['HIRC']
    n = struct.unpack('<I', d[o:o+4])[0]
    p = o + 4
    objs = []
    for _ in range(n):
        t = d[p]; sz = struct.unpack('<I', d[p+1:p+5])[0]
        oid = struct.unpack('<I', d[p+5:p+9])[0]
        objs.append((t, oid, d[p+9:p+5+sz]))
        p += 5 + sz
    return objs

if __name__ == '__main__':
    d, secs = parse(sys.argv[1])
    print({k: v[1] for k, v in secs.items()})
    ix = didx(d, secs)
    print('embedded wem:', len(ix))
    c = collections.Counter(t for t, _, _ in hirc(d, secs))
    print('hirc types:', dict(c))
