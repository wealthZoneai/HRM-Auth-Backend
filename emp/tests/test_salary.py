from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class SalaryTests(APITestCase):
    def setUp(self):
        self.emp = User.objects.create_user(
            username='sal_emp', password='spass',
            role='employee', email='sal@example.com'
        )
        self.client = APIClient()

    def token(self):
        url = reverse('token_obtain_pair')
        r = self.client.post(url, {
            'username': 'sal_emp', 'password': 'spass'
        }, format='json')
        return r.data['access']

    def test_get_my_salary(self):
        access = self.token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        url = reverse('my-salary')  # correct from emp/urls.py

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('salary', r.data)
