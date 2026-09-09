from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DeliveryResult:
    channel: str
    status: str


class NotificationChannel(Protocol):
    name: str

    def deliver(self, notification_id: str) -> DeliveryResult:
        ...


class InAppChannel:
    name = "IN_APP"

    def deliver(self, notification_id: str) -> DeliveryResult:
        return DeliveryResult(channel=self.name, status="stored")


class PushChannel:
    name = "PUSH"

    def deliver(self, notification_id: str) -> DeliveryResult:
        return DeliveryResult(channel=self.name, status="unavailable")
