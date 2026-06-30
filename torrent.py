"""
AI-SHIP — Torrent Creator
Creates .torrent files using the torf library.
Pure Python — no libtorrent needed.
"""
import os
from config import TORRENTS_DIR, DEFAULT_TRACKERS

try:
    import torf
    HAS_TORF = True
except ImportError:
    HAS_TORF = False


def create_torrent(source_path, name=None, trackers=None, output_path=None):
    """
    Create a .torrent file for a directory or file.

    Args:
        source_path:   Directory or file to torrent
        name:           Display name in the torrent (default: basename of source_path)
        trackers:       List of tracker announce URLs
        output_path:    Where to save the .torrent (default: torrents/<name>.torrent)

    Returns:
        (torrent_output_path, magnet_uri_str)
    """
    if not HAS_TORF:
        raise RuntimeError(
            "torf is not installed. Run: pip install torf\n"
            "Fallback pure-Python bittorrent creation is planned."
        )

    name = name or os.path.basename(os.path.abspath(source_path))
    trackers = trackers or DEFAULT_TRACKERS

    if output_path is None:
        os.makedirs(TORRENTS_DIR, exist_ok=True)
        output_path = os.path.join(TORRENTS_DIR, f"{name}.torrent")

    t = torf.Torrent(name=name)
    t.path = source_path          # source directory/file
    t.trackers = trackers
    t.generate(threads=1)         # hash all pieces
    t.write(output_path, overwrite=True)

    return output_path, str(t.magnet())


def create_torrent_for_dir(dir_path, name=None, trackers=None, output_dir=None):
    """Convenience: torrent an entire directory."""
    name = name or os.path.basename(os.path.abspath(dir_path))
    out_dir = output_dir or TORRENTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, f"{name}.torrent")
    return create_torrent(dir_path, name=name, trackers=trackers,
                          output_path=output_path)


def read_torrent_info(torrent_path):
    """Read info from an existing .torrent file. Returns (name, size_bytes, infohash)."""
    t = torf.Torrent.read(torrent_path)
    return t.name, t.size, t.infohash


def get_magnet(torrent_path):
    """Get magnet URI string from an existing .torrent file."""
    t = torf.Torrent.read(torrent_path)
    return str(t.magnet())
