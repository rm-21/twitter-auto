import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def _setup_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def get_cookies(
    email: str,
    username: str,
    password: str,
) -> list[dict[Any, Any]] | None:
    driver = _setup_driver()
    wait = WebDriverWait(driver, 10)  # 10 second timeout

    try:
        driver.get("https://x.com/login")

        # Step 1: Enter email
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_field.send_keys(email)

        next_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
        )
        next_button.click()

        # Step 2: Handle verification
        try:
            verify_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
            verify_field.send_keys(username)

            next_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            )
            next_button.click()
        except Exception as exc:
            print(exc)
            # Keep the long wait for potential manual verification
            time.sleep(120)
            pass

        # Step 3: Enter password
        password_field = wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)

        login_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
        )
        login_button.click()

        # Keep longer waits for post-login actions
        time.sleep(10)
        cookies = driver.get_cookies()

        return cookies

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        pass

    return None
