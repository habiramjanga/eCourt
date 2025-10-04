# middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
import threading

class CloseDriverOnSessionEnd(MiddlewareMixin):
    def process_response(self, request, response):
        # Close driver when the session ends
        session_key = getattr(request, 'session', {}).get('session_key')
        if session_key:
            from .views import user_drivers, user_drivers_lock, is_driver_valid
            with user_drivers_lock:
                if session_key in user_drivers and not is_driver_valid(user_drivers[session_key]['driver']):
                    driver = user_drivers[session_key]['driver']
                    driver.quit()
                    del user_drivers[session_key]
        return response
