from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class TLTests(APITestCase):
    def setUp(self):
        self.tl = User.objects.create_user(
            username='tlmain', password='tlp', role='tl', email='tlmain@example.com')
        self.tl.set_password('tlp')
        self.tl.save()

        self.emp = User.objects.create_user(
            username='tm1', password='tmp',
            role='employee', email='tm1@example.com'
        )
        
        self.emp.employeeprofile.team_lead = self.tl
        self.emp.employeeprofile.save()

        self.client = APIClient()

    def token(self):
        r = self.client.post('/api/login/', {
            'username': 'tlmain',
            'password': 'tlp'
        }, format='json')
        return r.data['access']

    def test_team_members(self):
        access = self.token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        # Direct path, because no name in tl/urls.py
        res = self.client.get('/api/team/members/')
        self.assertIn(res.status_code, (200, 204))
