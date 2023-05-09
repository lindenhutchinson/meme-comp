from django.contrib.auth import get_user_model
import random
import string

def generate_random_string(length):
    """Generate a random string up to the given maximum length."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def get_current_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            pass
    return None
