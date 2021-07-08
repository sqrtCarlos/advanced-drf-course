from django.test import TestCase
from django.contrib.auth import get_user_model


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
