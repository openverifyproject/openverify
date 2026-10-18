"""Windows child supervisor: create a kill-on-close job before launching tool code.

The supervisor owns the sole job handle. Termination/timeout closes that handle in
the OS, killing descendants even if the original tool parent has already exited.
This is process lifetime management, not a security sandbox.
"""

import ctypes
import os
import subprocess
import sys
from ctypes import wintypes


class BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_int64),
        ("job_time", ctypes.c_int64),
        ("flags", wintypes.DWORD),
        ("minimum", ctypes.c_size_t),
        ("maximum", ctypes.c_size_t),
        ("active", wintypes.DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority", wintypes.DWORD),
        ("scheduling", wintypes.DWORD),
    ]


class IoCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in (
            "read_ops",
            "write_ops",
            "other_ops",
            "read_bytes",
            "write_bytes",
            "other_bytes",
        )
    ]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("basic", BasicLimits),
        ("io", IoCounters),
        ("process_memory", ctypes.c_size_t),
        ("job_memory", ctypes.c_size_t),
        ("peak_process", ctypes.c_size_t),
        ("peak_job", ctypes.c_size_t),
    ]


def main() -> int:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateJobObjectW
    create.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    create.restype = wintypes.HANDLE
    set_info = kernel.SetInformationJobObject
    set_info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    set_info.restype = wintypes.BOOL
    assign = kernel.AssignProcessToJobObject
    assign.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    assign.restype = wintypes.BOOL
    current = kernel.GetCurrentProcess
    current.restype = wintypes.HANDLE
    handle = create(None, None)
    limits = ExtendedLimits()
    limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if (
        not handle
        or not set_info(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits))
        or not assign(handle, current())
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    # Job inheritance starts before any provider executable can create descendants.
    return subprocess.call(sys.argv[1:])


if __name__ == "__main__":
    os._exit(main())
