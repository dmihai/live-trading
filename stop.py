import psutil
import os
import signal


script = 'main.py'

for q in psutil.process_iter():
    if q.name().startswith('python'):
        if len(q.cmdline()) > 1 and script in q.cmdline()[1] and q.pid != os.getpid():
            print(f"Stopping process with PID {q.pid}")
            os.kill(q.pid, signal.SIGTERM)
