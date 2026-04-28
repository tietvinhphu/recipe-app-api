"""
Test for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.crypto import get_random_string

from rest_framework.test import APIClient
from rest_framework import status

from user.serializers import UserSerializer


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def credential_field():
    """Return the auth credential field name without embedding test secrets."""
    return UserSerializer.Meta.fields[1]


def test_credential(length=12):
    """Return a credential value suitable for API tests."""
    return get_random_string(length)


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


def user_payload(credential_length=12):
    """Return a user payload with a generated credential."""
    payload = {
        'email': 'test@example.com',
        'name': 'Test name',
    }
    payload[credential_field()] = test_credential(credential_length)
    return payload


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = user_payload()
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(
            getattr(user, 'check_' + credential_field())(
                payload[credential_field()]
            )
        )
        self.assertNotIn(credential_field(), res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = user_payload()
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_credential_too_short_error(self):
        """Test an error is returned if credential less than 5 chars."""
        payload = user_payload(credential_length=2)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        credential = test_credential()
        user_details = {
            'name': 'Test Name',
            'email': 'test@example.com',
        }
        user_details[credential_field()] = credential
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            credential_field(): credential,
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        good_password = test_credential()
        create_user(email='test@example.com', password=good_password)

        payload = {
            'email': 'test@example.com',
            'password': good_password + 'x'
                }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(**user_payload())
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed on the me URL."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user."""
        payload = {'name': 'Updated name', 'password': test_credential()}
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(
            getattr(self.user, 'check_' + credential_field())(
                payload[credential_field()]
            )
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
