from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileTests(APITestCase):
    def setUp(self):
        self.emp = User.objects.create_user(
            username='prof_emp', password='ppass',
            role='employee', email='prof@example.com'
        )
        self.client = APIClient()

    def token(self):
        url = reverse('token_obtain_pair')
        r = self.client.post(url, {
            'username': 'prof_emp',
            'password': 'ppass'
        }, format='json')
        return r.data['access']

    def test_update_contact(self):
        access = self.token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        # Correct URL name: my-profile-contact
        url = reverse('my-profile-contact')

        payload = {
            "personal_email": "new@example.com",
            "phone_number": "9876543210"
        }

        res = self.client.patch(url, payload, format='json')
        self.assertIn(res.status_code, (200, 202))
