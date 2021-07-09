from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
from PIL import Image
import tempfile
import os


RECIP_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id) -> str:
    # Return URL where the image will be uploaded
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def sample_tag(user, name='Main course') -> Tag:
    # Create and return a tag
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon') -> Ingredient:
    # Create and return an ingredient
    return Ingredient.objects.create(user=user, name=name)


def detail_url(recipe_id):
    # Return recipe detail url
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **params) -> Recipe:
    # Create and return recipe
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """
    Test access unauthenticated to the API
    """
    def setUp(self) -> None:
        self.client = APIClient()

    def test_required_auth(self):
        # Test required authentication
        res = self.client.get(RECIP_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """
    Test access authenticated to the API
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@email.com',
            password='12345qwe'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        # Test get recipes list
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        res = self.client.get(RECIP_URL)
        recipes = Recipe.objects.all().order_by('id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        # Test get a recipe for a user
        user_2 = get_user_model().objects.create_user(
            email='testu@email.com',
            password='1234qwerty'
        )
        sample_recipe(user=self.user)
        sample_recipe(user=user_2)
        res = self.client.get(RECIP_URL)
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        # Test to see the details of a recipe
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        # Test create recipe
        payload = {
            'title': 'Test recipe',
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIP_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        # Test create recipe with tags
        tag_1 = sample_tag(user=self.user, name='Tag 1')
        tag_2 = sample_tag(user=self.user, name='Tag 2')
        payload = {
            'title': 'Test recipe with tags',
            'tags': [tag_1.id, tag_2.id],
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIP_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_1, tags)
        self.assertIn(tag_2, tags)

    def test_create_recipe_with_ingredients(self):
        # Test create recipe with ingredients
        ingredient_1 = sample_ingredient(user=self.user, name='Ingredient 1')
        ingredient_2 = sample_ingredient(user=self.user, name='Ingredient 2')
        payload = {
            'title': 'Test recipe with ingredients',
            'ingredients': [ingredient_1.id, ingredient_2.id],
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(RECIP_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_1, ingredients)
        self.assertIn(ingredient_2, ingredients)


class RecipeImageUploadTests(TestCase):
    """
    Test the upload image cases
    """
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='testimage@email.com',
            password='12345qwe'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        # Test upload an image to the recipe
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        # Test upload image fail
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        # Test filter recipes by tag
        recipe_1 = sample_recipe(user=self.user, title='Thai vegetable curry')
        recipe_2 = sample_recipe(user=self.user, title='Aubergine with tahini')
        tag_1 = sample_tag(user=self.user, name='Vegan')
        tag_2 = sample_tag(user=self.user, name='Vegetarian')
        recipe_1.tags.add(tag_1)
        recipe_2.tags.add(tag_2)
        recipe_3 = sample_recipe(user=self.user, title='Fish and chips')
        res = self.client.get(
            RECIP_URL,
            {'tags': '{},{}'.format(tag_1.id, tag_2.id)}
        )
        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)

    def test_filter_recipes_by_ingredients(self):
        # Test filter recipes by ingredient
        recipe_1 = sample_recipe(user=self.user, title='Posh beans on toast')
        recipe_2 = sample_recipe(user=self.user, title='Chicken cacciatore')
        ingredient_1 = sample_ingredient(user=self.user, name='Feta cheese')
        ingredient_2 = sample_ingredient(user=self.user, name='Chicken')
        recipe_1.ingredients.add(ingredient_1)
        recipe_2.ingredients.add(ingredient_2)
        recipe_3 = sample_recipe(user=self.user, title='Steak and mushrooms')
        res = self.client.get(
            RECIP_URL,
            {'ingredients': '{},{}'.format(ingredient_1.id, ingredient_2.id)}
        )
        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)

        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)
