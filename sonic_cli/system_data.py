import psutil
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class CpuCore:
    """
    Contains the CPU core number and the current usage as a percentage.
    """

    number: int
    usage: float


@dataclass
class CpuCoresUsage:
    cpu_cores: List[CpuCore]
    average_usage_last_minute: float
    average_usage_last_5_minutes: float
    average_usage_last_15_minutes: float

    def __repr__(self) -> str:
        result = []
        for cpu_core in self.cpu_cores:
            result.append(f"core {cpu_core.number} usage {cpu_core.usage}")
        result.append(
            f"CPU usage average 1 min: {self.average_usage_last_minute}"
        )
        result.append(
            f"CPU usage average 5 min: {self.average_usage_last_5_minutes}"
        )
        result.append(
            f"CPU usage average 15 min: {self.average_usage_last_15_minutes}"
        )
        return "\n".join(result)

    def _str__(self) -> str:
        return self.__repr__()


@dataclass
class MemoryUsage:
    """
    Contains the CPU core number and the current usage as a percentage.



    total: total physical memory (exclusive swap).
    available: the memory that can be given instantly to processes without the system going into swap. This is calculated by summing different memory metrics that vary depending on the platform. It is supposed to be used to monitor actual memory usage in a cross platform fashion.
    percent: the percentage usage calculated as (total - available) / total * 100.
    used: memory used, calculated differently depending on the platform and designed for informational purposes only. total - free does not necessarily match used.
    free: memory not being used at all (zeroed) that is readily available; note that this doesn’t reflect the actual memory available (use available instead). total - used does not necessarily match free.
    active (UNIX): memory currently in use or very recently used, and so it is in RAM.
    inactive (UNIX): memory that is marked as not used.
    buffers (Linux, BSD): cache for things like file system metadata.
    cached (Linux, BSD): cache for various things.
    shared (Linux, BSD): memory that may be simultaneously accessed by multiple processes.
    slab (Linux): in-kernel data structures cache.
    """

    total: int
    available: int
    percent: float
    used: int
    free: int
    active: Optional[int]
    inactive: Optional[int]
    buffers: Optional[int]
    cached: Optional[int]
    shared: Optional[int]
    slab: Optional[int]

    @property
    def total_memory_in_gb(self) -> str:
        return f"{self.total / (1024 ** 3):.2f}"

    @property
    def available_memory_in_gb(self) -> str:
        return f"{self.available / (1024 ** 3):.2f}"

    @property
    def used_memory_in_gb(self) -> str:
        return f"{self.used / (1024 ** 3):.2f}"

    @property
    def free_memory_in_gb(self) -> str:
        return f"{self.free / (1024 ** 3):.2f}"

    @property
    def memory_usage_percentage(self) -> str:
        return f"{self.free / (1024 ** 3):.2f}"


def get_cpu_cores() -> CpuCoresUsage:
    """
    Retrieve the values of the CPU cores on the devices using psutil.

    Also displays the average CPU usage of the last few minutes.
    """
    # Return the average system load over the last 1, 5 and 15 minutes as a tuple. T
    (
        average_usage_last_minute,
        average_usage_last_5_minutes,
        average_usage_last_15_minutes,
    ) = psutil.getloadavg()
    cpu_cores = CpuCoresUsage(
        cpu_cores=[],
        average_usage_last_minute=average_usage_last_minute,
        average_usage_last_5_minutes=average_usage_last_5_minutes,
        average_usage_last_15_minutes=average_usage_last_15_minutes,
    )
    cpu_usages = psutil.cpu_percent(interval=1, percpu=True)

    for i, usage in enumerate(cpu_usages):
        cpu_core = CpuCore(number=i, usage=usage)
        cpu_cores.cpu_cores.append(cpu_core)

    return cpu_cores


def get_memory_usage() -> MemoryUsage:
    """
    Retrieve the virtual memory usage on the device using psutil.
    https://psutil.readthedocs.io/en/latest/#psutil.virtual_memory
    """

    memory_info = psutil.virtual_memory()

    return MemoryUsage(
        total=memory_info.total,
        available=memory_info.available,
        percent=memory_info.percent,
        used=memory_info.used,
        free=memory_info.free,
        active=getattr(memory_info, "active", None),
        inactive=getattr(memory_info, "inactive", None),
        buffers=getattr(memory_info, "buffers", None),
        cached=getattr(memory_info, "cached", None),
        shared=getattr(memory_info, "shared", None),
        slab=getattr(memory_info, "slab", None),
    )



