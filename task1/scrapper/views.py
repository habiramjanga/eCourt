from django.http import HttpResponse
from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
import time
from bs4 import BeautifulSoup

# Global driver variables
driver = None
wait = None

# Lazy driver initializer
def ensure_driver():
    global driver, wait
    try:
        if driver is None or driver.session_id is None:
            chrome_options = webdriver.ChromeOptions()
            # Optional headless mode
            # chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 20)

            # Load main page and click Case Status to initialize session
            driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
            wait.until(lambda d: d.find_element(By.CSS_SELECTOR, "a[href*='casestatus/index']"))
            driver.find_element(By.CSS_SELECTOR, "a[href*='casestatus/index']").click()
        else:
            # Check if current window is still open
            driver.current_url
    except (WebDriverException, NoSuchWindowException):
        # Reinitialize driver if session/window is closed
        driver = None
        wait = None
        return ensure_driver()
    return driver, wait

def home(request):
    return render(request, 'home.html')

def select_state(request):
    driver, wait = ensure_driver()
    if request.method == "POST":
        # Click "Case Status" link if not already on the page
        try:
            case_status_link = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='casestatus/index']"))
            )
            case_status_link.click()
        except:
            pass  # Already on casestatus page
        
        # Fetch states
        state_select_elem = wait.until(EC.presence_of_element_located((By.ID, "sess_state_code")))
        state_select = Select(state_select_elem)
        states = [opt.text.strip() for opt in state_select.options if opt.text.strip()]

        return render(request, 'states.html', {'states': states})
    return HttpResponse("Invalid request")

def select_dist(request):
    driver, wait = ensure_driver()
    selected_state = request.POST.get("state") if request.method == "POST" else None

    if not selected_state:
        return render(request, "districts.html", {"districts": [], "error": "No state selected"})

    # Select state
    state_select_elem = wait.until(EC.presence_of_element_located((By.ID, "sess_state_code")))
    Select(state_select_elem).select_by_visible_text(selected_state)

    # Wait for districts to populate
    district_select_elem = wait.until(lambda d: d.find_element(By.ID, "sess_dist_code"))
    wait.until(lambda d: len(Select(district_select_elem).options) > 1)

    district_select = Select(district_select_elem)
    districts = [opt.text.strip() for opt in district_select.options if opt.text.strip()]

    return render(request, "districts.html", {"districts": districts, "state": selected_state})

def court_complex(request):
    driver, wait = ensure_driver()
    selected_district = request.POST.get("district") if request.method == "POST" else None

    if not selected_district:
        return render(request, "complex.html", {"court_complexes": [], "error": "No district selected"})

    # Select district
    district_select_elem = wait.until(EC.presence_of_element_located((By.ID, "sess_dist_code")))
    Select(district_select_elem).select_by_visible_text(selected_district)

    # Wait for court complexes to populate
    court_complex_select_elem = wait.until(lambda d: d.find_element(By.ID, "court_complex_code"))
    wait.until(lambda d: len(Select(court_complex_select_elem).options) > 1)

    court_complex_select = Select(court_complex_select_elem)
    court_complexes = [opt.text.strip() for opt in court_complex_select.options if opt.text.strip()]


    return render(request, "complex.html", {"court_complexes": court_complexes, "district": selected_district})

def case_details(request):
    driver, wait = ensure_driver()

    if request.method == "POST":
        # Get selected court complex from previous form
        selected_court = request.POST.get("court_complex")
        if not selected_court:
            return render(request, "complex.html", {
                "court_complexes": [], 
                "error": "No court complex selected"
            })

        # Select the court complex in Selenium
        court_select = wait.until(EC.presence_of_element_located((By.ID, "court_complex_code")))
        Select(court_select).select_by_visible_text(selected_court)

        # Click "Case Number" tab to load case types
        button = wait.until(EC.element_to_be_clickable((By.ID, "casenumber-tabMenu")))
        driver.execute_script("arguments[0].click();", button)

        # Wait for the case type select to appear and load options
        case_type_select = wait.until(EC.presence_of_element_located((By.ID, "case_type")))
        wait.until(lambda d: len(Select(case_type_select).options) > 1)  # ensure options are loaded

        select_obj = Select(case_type_select)
        case_types = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]

        return render(request, "case_details.html", {"case_types": case_types, "selected_court": selected_court})

    # If GET, just render court selection page
    return render(request, "complex.html", {"court_complexes": [], "error": None})

def enter_captcha(request):
    driver, wait = ensure_driver()

    # Wait for captcha image
    captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha_image")))
    captcha_src = captcha_img.get_attribute("src")

    return render(request, "captcha.html", {"captcha_src": captcha_src})

def results(request):
    # Ensure driver & wait
    driver, wait = ensure_driver()

    # Wait for captcha image
    captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha_image")))
    captcha_src = captcha_img.get_attribute("src")

    if request.method == "POST":
        user_captcha = request.POST.get("captcha_input")

        # Enter captcha
        captcha_input = driver.find_element(By.ID, "case_captcha_code")
        captcha_input.clear()
        captcha_input.send_keys(user_captcha)

        # Trigger JS events
        for event in ["input", "change", "keyup"]:
            driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{event}', {{ bubbles: true }}));",
                captcha_input,
            )

        time.sleep(1)  # small pause
        driver.execute_script("submitCaseNo();")
        time.sleep(2)  # wait for results

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Check if captcha failed
        new_captcha_img = soup.find("img", {"id": "captcha_image"})
        if new_captcha_img:
            return render(request, "captcha.html", {
                "captcha_src": captcha_src,
                "error": "Incorrect captcha, please try again."
            })

        # ------------------------
        # Parse page data
        # ------------------------
        # Court info
        court_name = soup.find("h2", {"id": "chHeading"}).get_text(strip=True)

        # Case details
        case_details_table = soup.find("table", {"class": "case_details_table"})
        case_info = {}
        for row in case_details_table.find_all("tr"):
            cols = row.find_all(["td", "th"])
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                case_info[key] = value

        # Case status
        status_table = soup.find("table", {"class": "case_status_table"})
        case_status = {}
        for row in status_table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                case_status[key] = value

        # Petitioner/Respondent
        petitioner_table = soup.find("table", {"class": "Petitioner_Advocate_table"})
        petitioner_list = [td.get_text(strip=True) for td in petitioner_table.find_all("td")]

        respondent_table = soup.find("table", {"class": "Respondent_Advocate_table"})
        respondent_list = [td.get_text(strip=True) for td in respondent_table.find_all("td")]

        # Acts
        acts_table = soup.find("table", {"class": "acts_table"})
        acts_list = []
        for row in acts_table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                acts_list.append({
                    "act": cols[0].get_text(strip=True),
                    "section": cols[1].get_text(strip=True)
                })

        # Processes
        process_table = soup.find("table", {"id": "process"})
        processes = []
        for row in process_table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                processes.append({
                    "id": cols[0].get_text(strip=True),
                    "title": cols[1].get_text(strip=True),
                    "date": cols[2].get_text(strip=True)
                })

        # Orders
        order_table = soup.find("table", {"class": "order_table"})
        orders = []
        for row in order_table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                link_tag = cols[2].find("a")
                orders.append({
                    "order_number": cols[0].get_text(strip=True),
                    "order_date": cols[1].get_text(strip=True),
                    "order_details": link_tag.get_text(strip=True) if link_tag else cols[2].get_text(strip=True),
                    "pdf_link": link_tag.get("onclick") if link_tag else None
                })

        # ------------------------
        # Combine all data
        # ------------------------
        case_data = {
            "court_name": court_name,
            "case_info": case_info,
            "case_status": case_status,
            "petitioner_list": petitioner_list,
            "respondent_list": respondent_list,
            "acts_list": acts_list,
            "processes": processes,
            "orders": orders
        }

        return render(request, "results.html", {"case_data": case_data})

    # GET request → show captcha
    return render(request, "captcha.html", {"captcha_src": captcha_src})






