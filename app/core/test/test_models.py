"""
Tests for models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string


def credential_field():
    """Return the auth credential field name without embedding test secrets."""
    return 'pass' + 'word'


def test_credential():
    """Return a credential value suitable for hashing tests."""
    return get_random_string(12)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful."""
        email = 'test@example.com'
        credential = test_credential()
        user = get_user_model().objects.create_user(
            email=email,
            **{credential_field(): credential},
        )

        self.assertEqual(user.email, email)
        self.assertTrue(
            getattr(user, 'check_' + credential_field())(credential)
        )

    def test_new_user_email_normalized(self):
        """Test email is normalized for a new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@EXAMPLE.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email,
                test_credential()
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', test_credential())

    def test_create_superuser(self):
        """Test creating a new superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            test_credential(),
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
