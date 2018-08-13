"""Configuration file for gunicorn."""

from prometheus_client import multiprocess


def child_exit(server, worker):  # type: ignore
    """Mark worker processes as dead for Prometheus when the worker exits.

    Note that this uses the child_exit hook instead of worker_exit so that it's handled
    by the master process (and will still be called if a worker crashes).
    """
    # pylint: disable=unused-argument
    multiprocess.mark_process_dead(worker.pid)
