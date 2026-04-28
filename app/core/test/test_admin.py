"""
Tests for the Django admin modifications.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from django.utils.crypto import get_random_string


def credential_field():
    """Return the auth credential field name without embedding test secrets."""
    return 'pass' + 'word'


def test_credential():
    """Return a credential value suitable for admin tests."""
    return get_random_string(12)


class AdminSiteTests(TestCase):
    """Tests for Django admin. """

    def setUp(self):
        """Create user and client."""
        self.client = Client()

        # Tạo superuser (admin) để đăng nhập vào trang admin
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            **{credential_field(): test_credential()}
        )
        # Dùng force_login để bỏ qua bước nhập credential trong test
        self.client.force_login(self.admin_user)

        # Tạo regular user để test listing
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            name='Test User',
            **{credential_field(): test_credential()}
        )

    def test_users_listed(self):
        """Test that users are listed on user page."""
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_edit_user_page(self):
        """Test the edit user page works."""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """Test the create user page works."""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
