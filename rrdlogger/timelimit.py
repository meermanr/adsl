#!/usr/bin/env python
"""
Run a given command and kill it after a specified amount of time (unless it has 
exited of its own accord). If the command is killed the process will exit with 
SIGKILL.

On Linux, exit due to SIGKILL manifests as exit code -9. This is sometimes 
mistakenly shown as 137 (the 8-bit 2's complement is being misinterpreted as an 
unsigned number).

:Variables:
    g_ph : subprocess.Popen
        Global process handle for the current process, or None (no process is 
        running).
    g_shoos : int
        Number of times the child process has been told to go away. Used to 
        decide what strength signal to kill it with.
"""
__docformat__ = "restructuredtext en"

import time
import signal

# =============================================================================
# GLOBALS
# =============================================================================
g_ph = None
g_shoos = 0

# -----------------------------------------------------------------------------
def sigalrm_handler(sig, frame):
    """
    Kill our child process, and then kill ourselves with SIGKILL. On Linux this 
    means our parent process will see our exit code as -9 (exit due to a signal 
    is negative, signal.SIGKILL == 9).
    """
    global g_ph
    global g_shoos

    import os

    del sig
    del frame

    g_shoos += 1

    # Kill child process
    if g_ph is not None:
        if g_shoos == 1:
            # First offence. Signal politely and wait for exit.
            signal.alarm(3) # Allow 3 seconds for termination
            g_ph.terminate()
            g_ph.wait()
        else:
            # Second offence. Signal harshly, don't wait.
            g_ph.kill()

    # Kill self
    pid = os.getpid()
    os.kill(pid, signal.SIGKILL)

# -----------------------------------------------------------------------------
def main():
    global g_ph

    import optparse
    import subprocess

    parser = optparse.OptionParser(
            usage="%prog [options] command [param [...]]",
            version="v1.0",
            description=__doc__,
            )

    parser.disable_interspersed_args()

    parser.add_option(
            "-t", "--timelimit",
            help="Number of seconds after which to kill the command",
            action="store", type=int,
            metavar="SECONDS",
            default=20,
            dest="timelimit",
            )

    opts, args = parser.parse_args()

    # Register a signal handler, than schedule a signal
    signal.signal(signal.SIGALRM, sigalrm_handler)
    signal.alarm(opts.timelimit)

    g_ph = subprocess.Popen(args, shell=False)
    retcod = g_ph.wait()    # (Doesn't block signals)

    # If SIGALRM has fired then the signal handler is now responsible for 
    # exiting.

    if g_shoos > 0:
        time.sleep(3600)
    else:
        exit(retcod)


# =============================================================================
if __name__ == "__main__":
    main()
