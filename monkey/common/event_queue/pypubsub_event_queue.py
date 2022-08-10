from typing import Callable

from common.events import AbstractEvent
from pubsub.core import Publisher

from .i_event_queue import IEventQueue

INTERNAL_ALL_EVENT_TYPES_TOPIC = "internal_all_event_types"


class PyPubSubEventQueue(IEventQueue):
    def __init__(self, pypubsub_publisher: Publisher):
        self._pypubsub_publisher = pypubsub_publisher

    def subscribe_all(self, subscriber: Callable[[AbstractEvent], None]):
        self._pypubsub_publisher.subscribe(
            listener=subscriber, topicName=INTERNAL_ALL_EVENT_TYPES_TOPIC
        )

    def subscribe_type(
        self, event_type: AbstractEvent, subscriber: Callable[[AbstractEvent], None]
    ):
        # pypubsub.pub.subscribe needs a string as the topic/event name
        self._pypubsub_publisher.subscribe(listener=subscriber, topicName=event_type.__name__)

    def subscribe_all_event_types(self, subscriber: Callable[[AbstractEvent], None]):
        self._pypubsub_publisher.subscribe(
            listener=subscriber, topicName=INTERNAL_ALL_EVENT_TYPES_TOPIC
        )

    def subscribe_tag(self, tag: str, subscriber: Callable[[AbstractEvent], None]):
        self._pypubsub_publisher.subscribe(listener=subscriber, topicName=tag)

    def publish(self, event: AbstractEvent):
        self._publish_to_all_events_topic(event)
        self._publish_to_type_topic(event)
        self._publish_to_tags_topic(event)

    def _publish_to_all_events_topic(self, event: AbstractEvent):
        self._pypubsub_publisher.sendMessage(INTERNAL_ALL_EVENT_TYPES_TOPIC, event=event)

    def _publish_to_type_topic(self, event: AbstractEvent):
        self._pypubsub_publisher.sendMessage(event.__name__, event=event)

    def _publish_to_tags_topic(self, event: AbstractEvent):
        for tag in event.tags:
            self._pypubsub_publisher.sendMessage(tag, event=event)
