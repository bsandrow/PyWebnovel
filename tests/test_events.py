from unittest import TestCase

from webnovel.events import Context, Event, EventRegistry


class EventRegistryTestCase(TestCase):
    def test_initializes_map(self):
        registry = EventRegistry()
        self.assertIsNotNone(registry._map)

    def test_register(self):
        def callback(context):
            pass

        registry = EventRegistry()
        registry.register(Event.SET_COVER_IMAGE, callback)
        self.assertEqual(registry._map[Event.SET_COVER_IMAGE], [callback])

    def test_trigger(self):
        test_data = {}

        def callback(context):
            test_data["was_called"] = True
            test_data["context"] = context

        registry = EventRegistry()
        registry.register(Event.SET_COVER_IMAGE, callback)
        registry.trigger(Event.SET_COVER_IMAGE, {"cover_image_url": ":URL:"})
        expected_context = Context(cover_image_url=":URL:")
        expected_context.event = Event.SET_COVER_IMAGE
        self.assertEqual(test_data, {"was_called": True, "context": expected_context})

    def test_clear(self):
        def callback(context):
            pass

        registry = EventRegistry()
        registry.register(Event.SET_COVER_IMAGE, callback)
        self.assertEqual(registry._map[Event.SET_COVER_IMAGE], [callback])
        registry.clear()
        self.assertEqual(registry._map[Event.SET_COVER_IMAGE], [])
