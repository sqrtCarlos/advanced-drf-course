from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag
from core.models import Recipe
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApisTests(TestCase):
    """
    Test tags API's public available
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        # Test login is required to get the tags
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """
    Test tags API's private available
    """

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email='test@email.com',
            password='12345qwe'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        # Test get tags
        Tag.objects.create(user=self.user, name='Meat')
        Tag.objects.create(user=self.user, name='Banana')
        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        # Test tags returned belong to the user
        user_2 = get_user_model().objects.create_user(
            email='user2@email.com',
            password='12345qwe'
        )
        Tag.objects.create(user=user_2, name='Raspberry')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        # Test create a new tag
        payload = {'name': 'Simple'}
        self.client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        # Test create a new tag with invalid payload
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        # Test filtering tags recipes based
        tag_1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag_2 = Tag.objects.create(user=self.user, name='Launch')
        recipe = Recipe.objects.create(
            title='Coriander eggs on toast',
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe.tags.add(tag_1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        serializer_1 = TagSerializer(tag_1)
        serializer_2 = TagSerializer(tag_2)

        self.assertIn(serializer_1.data, res.data)
        self.assertNotIn(serializer_2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        # Test filter filter tags assigned by unique elements
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        recipe_1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=3.00,
            user=self.user
        )
        recipe_1.tags.add(tag)
        recipe_2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=2.00,
            user=self.user
        )
        recipe_2.tags.add(tag)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
