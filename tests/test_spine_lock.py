"""Single-instance law (O5_INPUTS §C/§J): a second start against the
same data root refuses with a distinct error; stale-lock recovery works
without PID bookkeeping (the OS releases a dead holder's lock).
"""

from app.spine.errors import SPINE_ALREADY_RUNNING
from app.spine.instance_lock import InstanceLock, LockHeld
from app.spine.server import run


def test_second_acquire_refuses(tmp_path):
    path = tmp_path / "spine.lock"
    first = InstanceLock(path)
    first.acquire()
    second = InstanceLock(path)
    try:
        second.acquire()
    except LockHeld:
        pass
    else:
        raise AssertionError("second acquire should refuse while held")
    finally:
        first.release()


def test_release_frees_the_lock(tmp_path):
    path = tmp_path / "spine.lock"
    first = InstanceLock(path)
    first.acquire()
    first.release()
    second = InstanceLock(path)
    second.acquire()  # must not raise
    second.release()


def test_stale_lock_file_recovers(tmp_path):
    # A crashed prior run leaves the file with no OS lock held — the
    # next start acquires it cleanly.
    path = tmp_path / "spine.lock"
    path.write_text("left behind by a dead process", encoding="utf-8")
    lock = InstanceLock(path)
    lock.acquire()
    assert lock.held
    lock.release()


def test_lock_is_a_context_manager(tmp_path):
    path = tmp_path / "spine.lock"
    with InstanceLock(path) as lock:
        assert lock.held
    follower = InstanceLock(path)
    follower.acquire()  # released on exit above
    follower.release()


def test_run_refuses_distinctly_while_an_instance_holds_the_root(
    tmp_path, capsys
):
    root = tmp_path / "root"
    root.mkdir(parents=True)
    holder = InstanceLock(root / "spine.lock")
    holder.acquire()
    try:
        assert run(root) == 1
    finally:
        holder.release()
    stderr = capsys.readouterr().err
    assert SPINE_ALREADY_RUNNING in stderr
