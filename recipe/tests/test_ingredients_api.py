from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTest(TestCase):
    """
    Test ingredients API's public access
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        # Test login is required to access to this endpoint
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    """
    Test ingredients API's private access
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@mail.com',
            password='12345qwe'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_list(self):
        # Test get ingredients list
        Ingredient.objects.create(user=self.user, name='kale')
        Ingredient.objects.create(user=self.user, name='salt')
        res = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        # Test return just ingredients for the user authenticated
        user_2 = get_user_model().objects.create_user(
            email='test2@mail.com',
            password='12345qwr'
        )
        Ingredient.objects.create(user=user_2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Pepper')
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        # Test create a new ingredient correctly
        payload = {'name': 'Onion'}
        res = self.client.post(INGREDIENT_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        # Test create a new ingredient with bad payload
        payload = {'name': ''}
        res = self.client.post(INGREDIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

