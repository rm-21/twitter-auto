import json
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

    # Enable logging
    options.set_capability(
        "goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"}
    )

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


def get_network_calls(driver: WebDriver) -> list[Any]:
    calls = []
    browser_log = driver.get_log("performance")
    for log in browser_log:
        if "message" not in log:
            continue

        log_entry = json.loads(log["message"])

        try:
            # Look for network requests
            if (
                "message" in log_entry
                and "method" in log_entry["message"]
                and log_entry["message"]["method"] == "Network.requestWillBeSent"
            ):
                url = log_entry["message"]["params"]["request"]["url"]
                if "client_event.json" in url:
                    calls.append(
                        {
                            "url": url,
                            "headers": log_entry["message"]["params"]["request"].get(
                                "headers", {}
                            ),
                            "timestamp": log_entry["message"]["params"].get(
                                "timestamp", ""
                            ),
                        }
                    )
        except Exception as e:
            print(f"Error processing log entry: {e}")
            continue

    return calls


def get_session_info(
    email: str,
    username: str,
    password: str,
) -> dict[str, str | None] | None:
    driver = _setup_driver()
    wait = WebDriverWait(driver, 10)
    network_calls = []

    try:
        # Enable CDP Network domain
        driver.execute_cdp_cmd("Network.enable", {})

        driver.get("https://x.com/login")

        # Complete login flow first
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_field.send_keys(email)

        next_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
        )
        next_button.click()

        try:
            verify_field = wait.until(EC.presence_of_element_located((By.NAME, "text")))
            verify_field.send_keys(username)

            next_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            )
            next_button.click()
        except Exception as exc:
            print(exc)
            time.sleep(120)
            pass

        password_field = wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)

        login_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
        )
        login_button.click()

        # Wait for login to complete and cookies to form
        time.sleep(10)
        cookies = driver.get_cookies()

        # Navigate to home to trigger events
        driver.get("https://x.com/home")
        time.sleep(5)  # Wait for potential events to trigger

        # Get network calls
        network_calls = get_network_calls(driver)

        auth_token = [cookie for cookie in cookies if cookie["name"] == "auth_token"][
            0
        ]["value"]
        csrf_token = [cookie for cookie in cookies if cookie["name"] == "ct0"][0][
            "value"
        ]

        bearer_token = None
        if network_calls:
            bearer_token = network_calls[0]["headers"]["authorization"].split(" ")[-1]

        return {
            "auth_token": auth_token,
            "csrf_token": csrf_token,
            "bearer_token": bearer_token,
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        try:
            driver.execute_cdp_cmd("Network.disable", {})
        except Exception:
            pass
        driver.quit()
