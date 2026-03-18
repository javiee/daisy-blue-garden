from django.test import TestCase
from apps.garden.models import GardenItem


class GardenItemModelTest(TestCase):
    def test_create_garden_item(self):
        item = GardenItem.objects.create(name='Rose', type='plant')
        self.assertEqual(str(item), 'Rose (plant)')

    def test_default_type(self):
        item = GardenItem.objects.create(name='Fern')
        self.assertEqual(item.type, 'plant')

    def test_description_blank_by_default(self):
        item = GardenItem.objects.create(name='Oak', type='tree')
        self.assertEqual(item.description, '')
        self.assertEqual(item.cares, '')

    def test_ordering_by_created_at_desc(self):
        item1 = GardenItem.objects.create(name='A', type='plant')
        item2 = GardenItem.objects.create(name='B', type='tree')
        items = list(GardenItem.objects.all())
        self.assertEqual(items[0], item2)
        self.assertEqual(items[1], item1)
