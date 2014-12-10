import os
import errno
import multiprocessing
from operator import isNumberType

from billiard._pool import Pool, worker


def pid_is_dead(pid):
    """Check if a process is not running by PID.

    :rtype bool:

    """
    try:
        return os.kill(pid, 0)
    except OSError, err:
        if err.errno == errno.ESRCH:
            return True # No such process.
        elif err.errno == errno.EPERM:
            return False # Operation not permitted.
        else:
            raise


def reap_process(pid):
    """Reap process if the process is a zombie.

    :returns: ``True`` if process was reaped or is not running,
        ``False`` otherwise.

    """
    if pid_is_dead(pid):
        return True

    try:
        is_dead, _ = os.waitpid(pid, os.WNOHANG)
    except OSError, err:
        if err.errno == errno.ECHILD:
            return False # No child processes.
        raise
    return is_dead


def process_is_dead(process):
    """Check if process is not running anymore.

    First it finds out if the process is running by sending
    signal 0. Then if the process is a child process, and is running
    it finds out if it's a zombie process and reaps it.
    If the process is running and is not a zombie it tries to send
    a ping through the process pipe.

    :param process: A :class:`multiprocessing.Process` instance.

    :returns: ``True`` if the process is not running, ``False`` otherwise.

    """

    # Only do this if os.kill exists for this platform (e.g. Windows doesn't
    # support it).
    if getattr(os, "kill", None) and reap_process(process.pid):
        return True

    # Then try to ping the process using its pipe.
    try:
        proc_is_alive = process.is_alive()
    except OSError:
        return True
    else:
        return not proc_is_alive


class DynamicPool(Pool):
    """Version of :class:`multiprocessing.Pool` that can dynamically grow
    in size."""

    def __init__(self, processes=None, initializer=None, initargs=()):

        super(DynamicPool, self).__init__(processes=processes,
                                          initializer=initializer,
                                          initargs=initargs)
        self.logger = multiprocessing.get_logger()

    def _my_cleanup(self):
        from multiprocessing.process import _current_process
        for p in list(_current_process._children):
            discard = False
            try:
                status = p._popen.poll()
            except OSError:
                discard = True
            else:
                if status is not None:
                    discard = True
            if discard:
                _current_process._children.discard(p)

    def add_worker(self):
        """Add another worker to the pool."""
        self._my_cleanup()
        worker = self._create_worker_process()
        self.logger.debug(
            "DynamicPool: Started pool worker %s (PID: %s, Poolsize: %d)" % (
                worker.name, worker.pid, len(self._pool)))

    def grow(self, size=1):
        """Add workers to the pool.

        :keyword size: Number of workers to add (default: 1)

        """
        [self.add_worker() for i in range(size)]

    def _is_dead(self, process):
        """Try to find out if the process is dead.

        :rtype bool:

        """
        if process_is_dead(process):
            self.logger.info("DynamicPool: Found dead process (PID: %s)" % (
                process.pid))
            return True
        return False

    def _bring_out_the_dead(self):
        """Sort out dead process from pool.

        :returns: Tuple of two lists, the first list with dead processes,
            the second with active processes.

        """
        dead, alive = [], []
        for process in self._pool:
            if process and process.pid and isNumberType(process.pid):
                if self._is_dead(process):
                    dead.append(process)
                else:
                    alive.append(process)
        return dead, alive

    def replace_dead_workers(self):
        """Replace dead workers in the pool by spawning new ones.

        :returns: number of dead processes replaced, or ``None`` if all
            processes are alive and running.

        """
        dead, alive = self._bring_out_the_dead()
        if dead:
            dead_count = len(dead)
            self._pool = alive
            self.grow(min(dead_count, self._size))
            return dead_count
