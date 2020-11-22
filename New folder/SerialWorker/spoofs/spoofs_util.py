import time
import os
import subprocess

def resolve_path(fname):
    try:
        from pathlib import Path
        return Path(fname).resolve()
    except:
        return os.path.realpath(fname)


def linux_start_port_spoof_bridge(p1,p2):
    proc = subprocess.Popen(["/usr/bin/socat", "PTY,link=%s", "PTY,link=%s" % (p1,p2)])
    time.sleep(1.0)
    real_path = resolve_path(p1)
    real_path2 = resolve_path(p2)
    os.system("chmod 664 %s" % (real_path))
    os.system("chmod 664 %s" % (real_path2))
    os.system("chown root:dialout %s" % (real_path))
    os.system("chown root:dialout %s" % (real_path2))
    return proc
