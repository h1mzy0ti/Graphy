import os
from django.conf import settings

def get_user_storage_usage(user):
    """
    Calculates the total size (in MB) of all files uploaded by the user.
    """
    user_path = os.path.join(settings.MEDIA_ROOT, 'uploads', user.username)
    total = 0
    if os.path.exists(user_path):
        for root, dirs, files in os.walk(user_path):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
    return round(total / (1024 ** 2), 2)  # Return size in MB
