from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKE_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """
    Test public API of the user
    """
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_valid_user_success(self):
        # Test create user with a success payload
        payload = {
            'email': 'test@email.com',
            'password': '123qwe',
            'name': 'Test Name'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_existing_user(self):
        # Test create a user that already exists
        payload = {
            'email': 'test@email.com',
            'password': 'test',
            'name': 'Test Name'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            'email': 'test@email.com',
            'password': 'pw',
            'name': 'Test Name'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_user(self):
        # Test token is created for the user
        payload = {
            'email': 'test@email.com',
            'password': '123qwe',
            'name': 'Test Name'
        }
        create_user(**payload)
        res = self.client.post(TOKE_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        # Test token is not created with invalid credentials
        create_user(email='test@mail.com', password='123qwe')
        payload = {'email': 'test@mail.com', 'password': 'wrong'}
        res = self.client.post(TOKE_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        # Test token is not created if a user doesn't exists
        payload = {
            'email': 'test@email.com',
            'password': '123qwe',
        }
        res = self.client.post(TOKE_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        # Test email and password are required
        res = self.client.post(TOKE_URL, {'email': 'one', 'password': ''})

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
