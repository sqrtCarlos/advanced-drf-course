from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models
from unittest.mock import patch


def sample_user(email='test@email.com', password='12345qwe'):
    # Create a test user
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):

    def test_create_user_with_email_successful(self):
        # Test create a new user with an email successfully
        email = 'test@email.com'
        password = 'test123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        # Test an email format for a new user
        email = 'test@EMAIL.com'
        user = get_user_model().objects.create_user(
            email=email,
            password='123qwe'
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        # New user with invalid email
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,
                password='123qwe'
            )

    def test_create_new_superuser(self):
        # Test superuser created
        email = 'test@email.com'
        password = 'test123'
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        # Test a str representation of tag text
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Meat'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        # Test a str representation of ingredient text
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Banana'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        # Test a str representation of recipe text
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=5.00
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        # Test image has been saved in the correct place
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_patch = models.recipe_image_file_path(None, 'myimage.jpg')
        exp_path = f'uploads/recipe/{uuid}.jpg'

        self.assertEqual(file_patch, exp_path)
