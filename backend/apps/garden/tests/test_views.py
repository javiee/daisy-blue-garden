from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from apps.garden.models import GardenItem


class GardenItemAPITest(APITestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(
            name='Rose', type='plant', description='A red rose'
        )

    @patch('apps.garden.signals.on_garden_item_created')
    def test_list_items(self, _):
        response = self.client.get('/api/v1/garden/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    @patch('apps.llm.tasks.generate_item_care_async')
    def test_create_item(self, mock_task):
        mock_task.delay = lambda pk: None
        data = {'name': 'Oak', 'type': 'tree'}
        response = self.client.post('/api/v1/garden/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GardenItem.objects.count(), 2)

    def test_get_item(self):
        response = self.client.get(f'/api/v1/garden/{self.item.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Rose')

    def test_update_item(self):
        data = {'name': 'Updated Rose', 'type': 'plant'}
        response = self.client.put(f'/api/v1/garden/{self.item.pk}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Updated Rose')

    def test_delete_item(self):
        response = self.client.delete(f'/api/v1/garden/{self.item.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_filter_by_type(self):
        GardenItem.objects.create(name='Oak', type='tree')
        response = self.client.get('/api/v1/garden/?type=tree')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_search(self):
        response = self.client.get('/api/v1/garden/?search=rose')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
