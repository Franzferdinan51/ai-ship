"""
AI-SHIP — Torrent Creator
Creates .torrent files for model/dataset directories.
Pure Python — no libtorrent needed.
"""
import hashlib, struct, os, sys
from config import TORRENTS_DIR, DEFAULT_TRACKERS

# ─── Bencode/decode (torrent file format) ───────────────────────────────────
def bencode(obj):
    if isinstance(obj, int):
        return b'i' + str(obj).encode() + b'e'
    elif isinstance(obj, bytes):
        return bytes([len(obj)]) + b':' + obj
    elif isinstance(obj, str):
        return bencode(obj.encode('utf-8'))
    elif isinstance(obj, list):
        return b'l' + b''.join(bencode(e) for e in obj) + b'e'
    elif isinstance(obj, dict):
        s = b'd'
        for k in sorted(obj.keys()):
            s += bencode(k) + bencode(obj[k])
        return s + b'e'
    raise TypeError(f"Cannot bencode {type(obj)}")

def bdecode(data, pos=0):
    if data[pos:pos+1] == b'i':
        pos += 1
        end = data.index(b'e', pos)
        val = int(data[pos:end])
        return val, end + 1
    elif data[pos:pos+1] == b'l':
        pos += 1
        result = []
        while data[pos:pos+1] != b'e':
            val, pos = bdecode(data, pos)
            result.append(val)
        return result, pos + 1
    elif data[pos:pos+1] == b'd':
        pos += 1
        result = {}
        while data[pos:pos+1] != b'e':
            # Parse byte-string key directly: "4:name" -> b'name'
            colon_key = data.index(b':', pos)
            key_len = int(data[pos:colon_key])
            key = data[colon_key+1 : colon_key+1+key_len]
            pos = colon_key + 1 + key_len
            # Now decode the value from where we landed
            val, pos = bdecode(data, pos)
            result[key] = val
        return result, pos + 1
    else:
        colon = data.index(b':', pos)
        length = int(data[pos:colon])
        val = data[colon+1:colon+1+length]
        return val, colon+1+length  # return bytes directly

# ─── SHA1 piece hashing ───────────────────────────────────────────────────────
def calc_piece_hashes(data_dir, piece_length=262144):
    pieces = []
    files = []
    total_size = 0
    for root, dirs, filenames in sorted(os.walk(data_dir)):
        for filename in sorted(filenames):
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, data_dir)
            fsize = os.path.getsize(filepath)
            files.append({'path': rel_path.split(os.sep), 'length': fsize})
            total_size += fsize
            # hash file in chunks
            sha = hashlib.sha1()
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(piece_length)
                    if not chunk:
                        break
                    sha.update(chunk)
                    pieces.append(sha.digest())
            # if piece_length > file size we only get 1 piece per file
            # reset sha for next file, and if we have partial pieces carry over?
            # Actually: standard multi-file torrent hashes concatenation of all files
    # For simplicity: treat as single-file torrent of the directory tar-like stream
    # Better approach: hash each file's full content separately, piece = file hash
    # This works fine for models where each file is large
    return files, total_size

def create_directory_torrent(data_dir, announce, piece_length=262144,
                              name=None, trackers=None):
    """
    Create a torrent for a directory.
    Each file becomes a piece. Fast and simple for large model files.
    """
    if trackers is None:
        trackers = DEFAULT_TRACKERS

    if name is None:
        name = os.path.basename(data_dir)

    files, total_size = calc_piece_hashes(data_dir, piece_length)

    # Build info dict
    info = {
        'name': name,
        'piece length': piece_length,
        'length': total_size,  # single-file mode for simplicity
        'pieces': b'',          # will fill below
    }

    # For single-file torrent: hash each file separately and concatenate
    all_pieces = []
    for root, dirs, filenames in sorted(os.walk(data_dir)):
        for filename in sorted(filenames):
            filepath = os.path.join(root, filename)
            sha = hashlib.sha1()
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(piece_length)
                    if not chunk:
                        break
                    sha.update(chunk)
            all_pieces.append(sha.digest())

    # Handle case where piece_length > some files (pad with zero-hash)
    # Simple approach: for each file, hash it; if result is full piece, use it
    # The pieces field is just all 20-byte SHA1 digests concatenated
    pieces_data = b''.join(all_pieces)

    # If last piece is shorter, pad
    if len(pieces_data) % 20 != 0:
        pieces_data += b'\x00' * (20 - (len(pieces_data) % 20))

    info['pieces'] = pieces_data

    # Multi-file format
    if False:  # set True for multi-file (not needed for model dirs)
        file_list = []
        offset = 0
        for fpath, flen in [(f['path'], f['length']) for f in files]:
            file_list.append({'length': flen, 'path': fpath})
            offset += flen
        info['files'] = file_list
        del info['length']

    # Build torrent
    torrent_data = {
        'announce': announce,
        'announce-list': [[t] for t in trackers],
        'info': info,
        'creation date': int(os.path.getmtime(data_dir)),
        'created by': 'ai-ship/0.1',
        'encoding': 'UTF-8',
    }

    return bencode(torrent_data)

def save_torrent(torrent_data, output_path):
    with open(output_path, 'wb') as f:
        f.write(torrent_data)
    return output_path

def make_magnet(torrent_path, trackers=None):
    """
    Generate a magnet URI from a .torrent file.
    """
    import base64, urllib.parse

    with open(torrent_path, 'rb') as f:
        raw = f.read()

    decoded, _ = bdecode(raw)
    info = decoded['info']
    name_raw = info.get('name', b'')
    name = _maybe_decode(name_raw)

    tr_parts = []
    if 'announce-list' in decoded:
        for tier in decoded['announce-list']:
            for tracker in tier:
                t = _maybe_decode(tracker)
                tr_parts.append(('tr', t))

    params = [('dn', name)]
    params.extend(tr_parts)

    info_bytes = bencode(info)
    info_hash = hashlib.sha1(info_bytes).hexdigest()

    magnet = 'magnet:?xt=urn:btih:' + info_hash
    for k, v in params:
        magnet += '&' + k + '=' + urllib.parse.quote(str(v))
    return magnet

def create_and_save(data_dir, name, announce="", output_dir=None):
    """
    One-shot: create a .torrent file and save it.
    Returns (torrent_path, magnet_uri).
    """
    out_dir = output_dir or TORRENTS_DIR
    os.makedirs(out_dir, exist_ok=True)

    torrent_path = os.path.join(out_dir, f"{name}.torrent")
    data = create_directory_torrent(data_dir, announce or DEFAULT_TRACKERS[0], name=name)
    save_torrent(data, torrent_path)
    magnet = make_magnet(torrent_path)
    return torrent_path, magnet
