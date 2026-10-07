from django.test import TestCase


class PlantIdentificationModelTest(TestCase):
    def test_defaults_to_pending_with_blank_fields(self):
        from apps.llm.models import PlantIdentification
        rec = PlantIdentification.objects.create()
        self.assertEqual(rec.status, 'pending')
        self.assertEqual(rec.name, '')
        self.assertEqual(rec.type, '')
        self.assertEqual(rec.description, '')
        self.assertEqual(rec.cares, '')
        self.assertEqual(rec.error, '')

    def test_valid_statuses(self):
        from apps.llm.models import PlantIdentification
        valid = [key for key, _ in PlantIdentification.STATUS_CHOICES]
        self.assertEqual(valid, ['pending', 'complete', 'failed'])

    def test_type_choices_match_garden_item(self):
        from apps.llm.models import PlantIdentification
        from apps.garden.models import GardenItem
        self.assertEqual(
            [key for key, _ in PlantIdentification.TYPE_CHOICES],
            [key for key, _ in GardenItem.TYPE_CHOICES],
        )
