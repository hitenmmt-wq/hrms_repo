# Create this file: hrms/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

# class EmailBackend(ModelBackend):
#     """
#     Custom authentication backend that allows users to log in using email instead of username.
#     """
#     def authenticate(self, request, username=None, password=None, email=None, **kwargs):
#         # Support both 'username' and 'email' parameters
#         email = email or username
#         print(f"==>> email: {email}")
        
#         if email is None or password is None:
#             return None
        
#         try:
#             # Get user by email
#             user = User.objects.get(email=email)
#             print(f"==>> user2233: {user}")
#         except User.DoesNotExist:
#             print("==>> User does not exist")
#             # Run the default password hasher once to reduce the timing
#             # difference between an existing and a nonexistent user
#             User().set_password(password)
#             return None
        
#         # Check password
#         print(f"==>> self.user_can_authenticate(user): {self.user_can_authenticate(user)}")
#         print(f"==>> user.check_password(password): {user.check_password(password)}")
#         if user.check_password(password) and self.user_can_authenticate(user):
#             print("==>> Authentication successful")
#             return user
#         print("==>> Authentication failed")
#         return None
    
#     def get_user(self, user_id):
#         try:
#             return User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return None
        
        
        