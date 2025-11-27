from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from emp.models import Attendance

User = get_user_model()


class AttendanceTests(APITestCase):
    def setUp(self):
        self.emp = User.objects.create_user(
            username='att_emp', password='apass',
            role='employee', email='att@example.com'
        )
        self.client = APIClient()

    def token(self):
        url = reverse('token_obtain_pair')
        res = self.client.post(url, {
            'username': 'att_emp',
            'password': 'apass'
        }, format='json')
        return res.data['access']

    def test_clock_in_and_out(self):
        access = self.token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        # Correct names from emp/urls.py
        url_in = reverse('clock-in')   # OK
        url_out = reverse('clock-out')  # OK

        r1 = self.client.post(url_in, {})
        self.assertIn(r1.status_code, (200, 201))

        r2 = self.client.post(url_out, {})
        self.assertIn(r2.status_code, (200, 201))

        self.assertTrue(Attendance.objects.filter(user=self.emp).exists())
