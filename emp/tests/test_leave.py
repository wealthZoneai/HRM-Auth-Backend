from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from emp.models import LeaveType, LeaveRequest, EmployeeProfile

User = get_user_model()


class LeaveTests(APITestCase):
    def setUp(self):
        self.hr = User.objects.create_user(
            username='hr1', password='hrpass', role='hr', email='hr1@example.com')
        self.tl = User.objects.create_user(
            username='tl1', password='tlpass', role='tl', email='tl1@example.com')
        self.emp = User.objects.create_user(
            username='empL', password='epass', role='employee', email='empL@example.com')

        # Assign TL as manager
        self.emp.employeeprofile.manager = self.tl
        self.emp.employeeprofile.save()

        self.lt = LeaveType.objects.create(name='Casual')

        self.client = APIClient()

    def token(self, u, p):
        url = reverse('token_obtain_pair')
        r = self.client.post(
            url, {'username': u, 'password': p}, format='json')
        return r.data['access']

    def test_leave_apply_and_tl_approve(self):
        access = self.token('empL', 'epass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        url = reverse('leave-apply')  # correct
        res = self.client.post(url, {
            "leave_type_id": self.lt.id,
            "start_date": "2025-10-01",
            "end_date": "2025-10-02",
            "days": "2",
            "reason": "Test"
        }, format='json')

        self.assertEqual(res.status_code, 201)

        leave_id = res.data['id']

        # TL Approves
        tl_token = self.token('tl1', 'tlpass')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tl_token}')

        action_url = reverse('tl-hr-leave-action',
                             kwargs={'leave_id': leave_id})

        a = self.client.post(action_url, {
            "action": "approve",
            "remarks": "ok"
        }, format='json')

        self.assertIn(a.status_code, (200, 201))
