from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from login.models import PasswordResetOTP

User = get_user_model()


class OTPTests(APITestCase):
    def setUp(self):
        self.emp = User.objects.create_user(
            username="otpuser",
            password="opass",
            email="otp@example.com",
            role="employee"
        )
        self.client = APIClient()

    def test_forgot_verify_reset(self):
        # Forgot password
        fp = reverse('forgot-password')
        r = self.client.post(fp, {"email": "otp@example.com"}, format='json')
        self.assertIn(r.status_code, (200, 201))

        otp_obj = PasswordResetOTP.objects.filter(user=self.emp).latest('id')

        # Verify OTP
        vo = reverse('verify-otp')
        r2 = self.client.post(vo, {
            "email": "otp@example.com",
            "otp": otp_obj.otp
        }, format='json')
        self.assertIn(r2.status_code, (200, 201))

        # Reset password
        rp = reverse('reset-password')
        r3 = self.client.post(rp, {
            "email": "otp@example.com",
            "new_password": "NewPass123!",
            "confirm_password": "NewPass123!"
        }, format='json')
        self.assertIn(r3.status_code, (200, 201))
