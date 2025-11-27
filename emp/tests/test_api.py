# emp/tests/test_api.py
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from emp.models import EmployeeProfile

User = get_user_model()

class HRMAPITests(APITestCase):
    def setUp(self):
        # create an HR user and a normal employee user
        self.hr_user = User.objects.create_user(username='hruser', password='hrpass', role='hr', email='hr@example.com')
        # ensure password is set properly
        self.hr_user.set_password('hrpass')
        self.hr_user.save()

        self.emp_user = User.objects.create_user(username='empuser', password='emppass', role='employee', email='emp@example.com')
        self.emp_user.set_password('emppass')
        self.emp_user.save()

        # API client
        self.client = APIClient()

    def obtain_token(self, username, password):
        """
        Obtain access token by calling your login endpoint.
        Ensure the URL name below matches your login URL name.
        """
        url = reverse('token_obtain_pair')  # expects name='token_obtain_pair' in login/urls.py
        resp = self.client.post(url, {'username': username, 'password': password}, format='json')
        self.assertEqual(resp.status_code, 200, msg=f"Login failed: {resp.status_code} {resp.data}")
        self.assertIn('access', resp.data, msg=f"No access token in login response: {resp.data}")
        return resp.data['access']

    def test_login_returns_token_and_role(self):
        access = self.obtain_token('hruser', 'hrpass')
        self.assertTrue(access)

    def test_hr_can_create_employee(self):
        access = self.obtain_token('hruser', 'hrpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        # Ensure the URL name below matches what you have in emp/urls.py
        url = reverse('hr-create-employee')
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "role": "employee",
            "emp_id": "TST123"
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, 201, msg=f"HR create employee failed: {resp.status_code} {resp.data}")
        # check profile exists
        self.assertTrue(EmployeeProfile.objects.filter(emp_id='TST123').exists())

    def test_employee_cannot_create_employee(self):
        access = self.obtain_token('empuser', 'emppass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        url = reverse('hr-create-employee')
        payload = {
            "first_name": "Bad",
            "last_name": "Actor",
            "role": "employee",
            "emp_id": "BAD123"
        }
        resp = self.client.post(url, payload, format='json')
        # permission denied expected (403 or 401)
        self.assertIn(resp.status_code, (401, 403), msg=f"Non-HR user unexpectedly allowed: {resp.status_code} {resp.data}")
