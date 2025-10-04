import os
import time
import base64
import logging
from datetime import datetime, timedelta
from threading import Lock

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, NoSuchElementException, TimeoutException,
    NoSuchWindowException, InvalidSessionIdException
)
from bs4 import BeautifulSoup
import requests

from .models import UserQueryLog

# Configure logging
logger = logging.getLogger(__name__)

# Global dictionaries for WebDriver sessions and locks
user_drivers = {}
session_locks = {}
user_drivers_lock = Lock()

def is_driver_valid(driver):
    """Check if the WebDriver session is still valid."""
    try:
        driver.current_url
        return True
    except (WebDriverException, NoSuchWindowException, InvalidSessionIdException):
        return False

def log_user_query(request, endpoint, response_data, status_code):
    """Log user queries and responses to the database."""
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

        UserQueryLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=None,  # No session key in token auth
            endpoint=endpoint,
            request_data=request.data if hasattr(request, 'data') else {},
            response_data=response_data,
            status_code=status_code,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception as e:
        logger.error(f"Error logging user query: {str(e)}")

def get_next_hearing_date(html_content):
    """Parse the next hearing date from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    next_hearing_date_str = None
    case_status_table = soup.find("table", class_="case_status_table")

    if case_status_table:
        rows = case_status_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 0 and "Next Hearing Date" in cells[0].get_text(strip=True):
                next_hearing_date_str = cells[1].get_text(strip=True)
                break

    if not next_hearing_date_str:
        return None, False

    try:
        for date_format in ["%d-%m-%Y", "%dth %B %Y", "%d %B %Y", "%d %b %Y", "%dth %b %Y"]:
            try:
                next_hearing_date = datetime.strptime(next_hearing_date_str, date_format)
                break
            except ValueError:
                continue
        else:
            try:
                day_part = next_hearing_date_str.split()[0].replace('th', '').replace('st', '').replace('nd', '').replace('rd', '')
                month_part = next_hearing_date_str.split()[1]
                year_part = next_hearing_date_str.split()[2]
                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12,
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                next_hearing_date = datetime(int(year_part), month_map[month_part], int(day_part))
            except Exception as e:
                logger.error(f"Error parsing date manually: {str(e)}")
                return next_hearing_date_str, False
    except Exception as e:
        logger.error(f"Error parsing date: {str(e)}")
        return next_hearing_date_str, False

    tomorrow = datetime.now() + timedelta(days=1)
    is_tomorrow = (
        next_hearing_date.day == tomorrow.day and
        next_hearing_date.month == tomorrow.month and
        next_hearing_date.year == tomorrow.year
    )
    return next_hearing_date_str, is_tomorrow

def ensure_driver(request, retries=2):
    """Ensure a WebDriver session is available for the current request."""
    user_id = request.user.id if request.user.is_authenticated else None
    if not user_id:
        return None, None

    if user_id not in session_locks:
        session_locks[user_id] = Lock()

    with session_locks[user_id]:
        # If already valid, reuse
        if user_id in user_drivers and is_driver_valid(user_drivers[user_id]['driver']):
            return user_drivers[user_id]['driver'], user_drivers[user_id]['wait']

        # Otherwise create a new one (with retry)
        for attempt in range(retries):
            try:
                chrome_options = webdriver.ChromeOptions()
                # chrome_options.add_argument("--headless=new")   # modern headless mode (better rendering)
                chrome_options.add_argument("--disable-logging")
                chrome_options.add_argument("--log-level=3")# The above code is using Chrome options
                # in Python to set various arguments for
                # the Chrome browser. These arguments
                # include setting the window size to
                # 1920x1080, disabling the GPU,
                # disabling the sandbox, and disabling
                # the shared memory usage for dev tools.
                # These options can be used when
                # creating a Chrome WebDriver instance
                # for automated testing or web scraping
                # purposes.
                
                # chrome_options.add_argument("--window-size=1920,1080")  # important for dropdowns/buttons
                # chrome_options.add_argument("--disable-gpu")
                # chrome_options.add_argument("--no-sandbox")
                # chrome_options.add_argument("--disable-dev-shm-usage")

                driver = webdriver.Chrome(options=chrome_options)
                wait = WebDriverWait(driver, 30)
                driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
                wait = WebDriverWait(driver, 20)

                # Click Case Status link to generate app_token
                driver.find_element(By.CSS_SELECTOR, "a[href*='casestatus/index']").click()

                user_drivers[user_id] = {'driver': driver, 'wait': wait}
                return driver, wait

            except Exception as e:
                logger.error(f"Driver creation attempt {attempt+1} failed: {e}")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(2)  # backoff before retry

        return None, None

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def register_user(request):
    """Register a new user."""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not all([username, password, email]):
            return Response(
                {"error": "Username, password, and email are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password)
        )

        return Response({
            "status": "success",
            "message": "User registered successfully.",
            "user_id": user.id,
            "username": user.username
        })
    except Exception as e:
        logger.error(f"Failed to register user: {str(e)}")
        return Response(
            {"error": f"Failed to register user: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def login_user(request):
    """Log in a user and return an auth token."""
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not all([username, password]):
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "status": "success",
                "message": "User logged in successfully.",
                "user_id": user.id,
                "username": user.username,
                "token": token.key
            })
        else:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        logger.error(f"Failed to log in: {str(e)}")
        return Response(
            {"error": f"Failed to log in: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Log out a user by deleting their token."""
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({"status": "success", "message": "Logged out successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"Failed to log out: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
def users(request):
    """Return a list of all users."""
    users = User.objects.all().values("id", "username", "email")
    return Response({"users": list(users)})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def close_driver(request):
    """Close the WebDriver session for the current user."""
    user_id = request.user.id
    if user_id not in user_drivers:
        return Response({"status": "No active session"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with session_locks[user_id]:
            if user_id in user_drivers:
                driver = user_drivers[user_id]['driver']
                driver.quit()
                del user_drivers[user_id]
        return Response({"status": "Driver closed"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to close driver: {str(e)}")
        return Response(
            {"error": f"Failed to close driver: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def driver_loader(request):
    """Handle GET/POST requests for states and districts."""
    user_id = request.user.id if request.user.is_authenticated else None
    if not user_id:
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        if request.method == 'GET':
            # Always reset driver when GET is called
            if user_id in user_drivers:
                try:
                    user_drivers[user_id]['driver'].quit()
                except Exception:
                    pass
                del user_drivers[user_id]

            # Try to create a fresh driver
            driver, wait = ensure_driver(request)
            if not driver:
                return Response({"error": "Failed to create driver"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            state_select_elem = wait.until(EC.presence_of_element_located((By.ID, "sess_state_code")))
            state_select = Select(state_select_elem)
            states = [opt.text.strip() for opt in state_select.options if opt.text.strip()]
            return Response({"states": states})

        elif request.method == 'POST':
            driver, wait = ensure_driver(request)
            if not driver:
                return Response({"error": "Driver not initialized"}, status=status.HTTP_400_BAD_REQUEST)

            statename = request.data.get('state')
            if not statename:
                return Response(
                    {"error": "State name is required in the POST data."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            state_select_elem = wait.until(EC.presence_of_element_located((By.ID, "sess_state_code")))
            state_select = Select(state_select_elem)
            state_select.select_by_visible_text(statename)
            time.sleep(2)

            district_select_elem = wait.until(EC.presence_of_element_located((By.ID, "sess_dist_code")))
            wait.until(lambda d: len(Select(district_select_elem).options) > 1)
            district_select = Select(district_select_elem)
            districts = [opt.text.strip() for opt in district_select.options if opt.text.strip()]
            return Response({"districts": districts})

    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        return Response({"error": f"Failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def set_district_and_get_courts(request):
    """Handle POST requests for districts and courts."""
    driver, wait = ensure_driver(request)
    if not driver:
        return Response({"error": "Driver not initialized"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        distname = request.data.get('district')
        if not distname:
            return Response(
                {"error": "District name is required in the POST data."},
                status=status.HTTP_400_BAD_REQUEST
            )

        district_select_elem = wait.until(EC.presence_of_element_located((By.ID, "sess_dist_code")))
        district_select = Select(district_select_elem)
        district_select.select_by_visible_text(distname)
        time.sleep(2)

        court_select_elem = wait.until(EC.presence_of_element_located((By.ID, "court_complex_code")))
        wait.until(lambda d: len(Select(court_select_elem).options) > 1)
        court_select = Select(court_select_elem)
        courts = [opt.text.strip() for opt in court_select.options if opt.text.strip()]
        return Response({"courts": courts})
    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        return Response(
            {"error": f"Failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def set_court_and_get_case_types(request):    
    """Handle POST requests for courts and case types."""    
    driver, wait = ensure_driver(request)    
    print("Session key from request:", request.data.get('session_key'))    
    try:        
        selected_court = request.data.get('court')        
        print("Selected court:", selected_court)        
        print("Session key from session:", request.session.session_key)        
        if not selected_court:            
            return Response(                
                {"error": "Court name is required in the POST data."},                
                status=status.HTTP_400_BAD_REQUEST            
                )        
        # Select the court        
        court_select = wait.until(EC.presence_of_element_located((By.ID, "court_complex_code")))        
        Select(court_select).select_by_visible_text(selected_court)        
        # # Click the "Case Number" tab to load case types        
        button = wait.until(EC.element_to_be_clickable((By.ID, "casenumber-tabMenu")))        
        driver.execute_script("arguments[0].click();", button)        
        # # Wait for the case type select to appear and load options        
        case_type_select = wait.until(EC.presence_of_element_located((By.ID, "case_type")))       
        wait.until(lambda d: len(Select(case_type_select).options) > 1)        
        select_obj = Select(case_type_select)        
        case_types = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]        
        # # Save the CAPTCHA image as a file        
        captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha_image")))        
        captcha_img.screenshot("captcha.png")        
        with open("captcha.png", "rb") as image_file:            
         encoded_captcha = base64.b64encode(image_file.read()).decode('utf-8')        
        os.remove("captcha.png")        
        return Response({            
        "case_types": case_types,            
        "captcha_image": f"data:image/png;base64,{encoded_captcha}"        
        })    
    except Exception as e:        
        print(f"Error: {e}")        
        return Response(            
            {"error": f"Failed to fetch case types: {str(e)}"},            
            status=status.HTTP_500_INTERNAL_SERVER_ERROR        
        )    
    finally:        
        pass  # Close driver if needed

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def post_case_inputs(request):
    """Handle POST requests for case inputs and return div content for frontend."""
    endpoint = "post_case_inputs"
    driver, wait = ensure_driver(request)
    if not driver:
        return Response({"error": "Driver not initialized"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Extract data from POST request
        case_type = request.data.get('case_type')
        case_number = request.data.get('case_number')
        case_year = request.data.get('case_year')
        captcha_text = request.data.get('captcha_text')

        # Input validation
        if not all([case_type, case_number, case_year, captcha_text]):
            response_data = {
                "error": "All fields (case_type, case_number, case_year, captcha_text) are required."
            }
            log_user_query(request, endpoint, response_data, status.HTTP_400_BAD_REQUEST)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        # Fill the form
        Select(wait.until(EC.presence_of_element_located((By.ID, "case_type")))).select_by_visible_text(case_type)
        driver.execute_script("document.getElementById('search_case_no').value = arguments[0];", case_number)
        driver.execute_script("document.getElementById('rgyear').value = arguments[0];", case_year)
        driver.execute_script("document.getElementById('case_captcha_code').value = arguments[0];", captcha_text)

        # Submit the form
        driver.execute_script("submitCaseNo();")

        # Wait for case links to appear and click them
        try:
            links = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.someclass"))
            )
            for link in links:
                js_call = link.get_attribute("onclick")
                if js_call:  # Ensure onclick attribute exists
                    driver.execute_script(js_call)
                    time.sleep(1)  # Small delay to avoid race conditions
        except Exception as e:
            logger.warning(f"Could not click case links: {str(e)}")

        # Wait for case details to load
        tab_content_div = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "CScaseNumber"))
        )
        html_content = tab_content_div.get_attribute("innerHTML")

        # Parse and clean HTML
        soup = BeautifulSoup(html_content, "html.parser")
        for element in soup(["script", "style", "orderheading", "table.order_table"]):
            element.decompose()

        # Extract next hearing date
        next_hearing_date_str, is_next_hearing = get_next_hearing_date(str(soup))

        # Fetch PDF URL
        pdf_url = None
        try:
            pdf_links = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@onclick,'displayPdf')]"))
            )
            if pdf_links:
                latest_pdf_link = pdf_links[-1]
                onclick_value = latest_pdf_link.get_attribute("onclick")
                if onclick_value:
                    driver.execute_script(onclick_value)
                    time.sleep(1)  # Wait for modal to load
                    modal_html = wait.until(
                        EC.presence_of_element_located((By.ID, "modal_order_body"))
                    ).get_attribute("outerHTML")
                    modal_soup = BeautifulSoup(modal_html, "html.parser")
                    pdf_object = modal_soup.find("object")
                    if pdf_object and pdf_object.has_attr("data"):
                        pdf_url = 'https://services.ecourts.gov.in/ecourtindia_v6/' + pdf_object["data"]
        except Exception as e:
            logger.error(f"Could not fetch PDF URL: {str(e)}")

        # Prepare response
        response_data = {
            "status": "success",
            "html_content": str(soup),
            "pdf_url": pdf_url,
            "next_hearing_date": next_hearing_date_str,
            "is_next_hearing_tomorrow": is_next_hearing
        }
        log_user_query(request, endpoint, response_data, status.HTTP_200_OK)
        return Response(response_data)

    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        response_data = {"error": f"Failed: {str(e)}"}
        log_user_query(request, endpoint, response_data, status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_latest_order(request):
    """Handle POST requests for downloading the latest order."""
    driver, wait = ensure_driver(request)
    if not driver:
        return Response({"error": "Driver not initialized"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        modal_html = wait.until(
            lambda d: d.find_element(By.ID, "modal_order_body")
        ).get_attribute("innerHTML")
        soup = BeautifulSoup(modal_html, "html.parser")
        pdf_object = soup.find("object")
        if not pdf_object:
            return Response(
                {"error": "PDF object not found in the modal"},
                status=status.HTTP_404_NOT_FOUND
            )

        pdf_url = 'https://services.ecourts.gov.in/ecourtindia_v6/' + pdf_object["data"]
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        resp = requests.get(pdf_url, cookies=cookies, verify=False)

        if resp.status_code == 200:
            response = HttpResponse(resp.content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="order.pdf"'
            return response
        else:
            return Response(
                {"error": f"Failed to download PDF. Status code: {resp.status_code}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        return Response(
            {"error": f"Failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if 'driver' in locals():
            driver.quit()

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_user_query_logs(request):
    """Retrieve user query logs."""
    try:
        logs = UserQueryLog.objects.filter(user=request.user).order_by('-request_timestamp')

        serialized_logs = []
        for log in logs:
            serialized_logs.append({
                'id': log.id,
                'endpoint': log.endpoint,
                'request_data': log.request_data,
                'response_data': log.response_data,
                'status_code': log.status_code,
                'request_timestamp': log.request_timestamp.isoformat(),
                'response_timestamp': log.response_timestamp.isoformat(),
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'user_id': log.user.id if log.user else None,
                'username': log.user.username if log.user else None
            })
        return Response({
            "status": "success",
            "logs": serialized_logs
        })
    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        return Response(
            {"error": f"Failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

