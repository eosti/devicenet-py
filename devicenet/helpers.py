from collections.abc import Callable
from dataclasses import dataclass

from devicenet.cid import DeviceNetCID


@dataclass
class CanFilter:
    id: int
    mask: int
    callback: Callable[[DeviceNetCID, bytes], None]

    def filter(self):
        return {"can_id": self.id, "can_mask": self.mask, "extended": False}
