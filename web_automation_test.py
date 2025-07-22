from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

WEB_UI_LOG_URL = "http://192.168.123.85"

PASSWORD = "admin"

CHROMEDRIVER_PATH = './chromedriver.exe'

ADMIN_ICON_LOCATOR = (By.XPATH, '//*[@id="img_admin"]')

POPUP_PASSWORD_FIELD_LOCATOR = (By.XPATH, '//*[@id="pwd"]')

POPUP_LOGIN_BUTTON_LOCATOR = (By.XPATH, '//*[@id="login_bt"]')

LOGOUT_BUTTON_LOCATOR = (By.XPATH, '//*[@id="top_optional"]/ul/li[4]')

CONFIRM_BUTTON_LOCATOR = (By.XPATH, '//*[@id="ext-gen294"]')

SUCCESS_LOGIN_INDICATOR = (By.XPATH, '//*[@id="33"]')

INVALID_PASSWORD_POPUP_LOCATOR = (By.XPATH, '//*[contains(text(), "Invalid Password")]')

INVALID_PASSWORD_OK_BUTTON_LOCATOR = (By.XPATH, '//*[@id="ext-comp-1002"]')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=CHROMEDRIVER_PATH)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def login_web_ui(driver, url, password, admin_icon_locator, pass_locator, login_btn_locator, success_indicator_locator, invalid_popup_locator, invalid_popup_ok_btn_locator):
    print(f"導航到登入頁面: {url}")
    driver.get(url)

    try:
        print("等待並點擊 'Admin' 圖示...")
        admin_icon = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(admin_icon_locator)
        )
        admin_icon.click()
        print("'Admin' 圖示已點擊。")

        print("等待彈出框的密碼輸入框出現...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(pass_locator)
        )

        print("輸入密碼....")
        password_field.send_keys(password)

        print("等待並點擊彈出框的登入/確認按鈕...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(login_btn_locator)
        )
        login_button.click()

        try:
            print("嘗試判斷登入結果...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(success_indicator_locator)
            )
            print("登入成功!已導向新頁面。")
            time.sleep(3)
            return True
        except TimeoutException:
            print("位在預期時間內導向新頁面, 檢查錯誤彈出框")
            try:
                error_popup = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(invalid_popup_locator)
                )
                print("偵測到 'Invalid Password' 彈出框!")
                ok_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(invalid_popup_ok_btn_locator)
                )
                ok_button.click()
                print("已點擊彈出框的OK按鈕。")
                driver.save_screenshot("login_failed_invalid_password.png")
                print("登入失敗:密碼錯誤。")
                return False
            except TimeoutException:
                print("登入失敗: 未知的登入問題(既沒導向新頁面, 也沒談出錯誤框)。")
                driver.save_screenshot("login_failed_unkown_issue.png")
                return False
    except Exception as e:
        print(f"登入流程發生一般錯誤: {e}")
        driver.save_screenshot("login_failed_unknown_issue.png")
        return False
    
def logout_web_ui(driver, logout_btn_locator, confirm_yes_btn_locator):
    try:
        print("等待點擊登出按鈕...")
        logout_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(logout_btn_locator)
        )
        logout_button.click()

        print("等待點擊彈出視窗的YES按鈕...")
        confirm_yes_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(confirm_yes_btn_locator)
        )
        confirm_yes_button.click()
        print("[是]按鈕已點擊。")

        print("登出成功!")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"登出失敗: {e}")
        return False
def main():
    driver = None
    try: 
        driver = setup_driver()
        if login_web_ui(driver, WEB_UI_LOG_URL, PASSWORD, ADMIN_ICON_LOCATOR, POPUP_PASSWORD_FIELD_LOCATOR, POPUP_LOGIN_BUTTON_LOCATOR, SUCCESS_LOGIN_INDICATOR, INVALID_PASSWORD_POPUP_LOCATOR, INVALID_PASSWORD_OK_BUTTON_LOCATOR):
            logout_web_ui(driver, LOGOUT_BUTTON_LOCATOR, CONFIRM_BUTTON_LOCATOR)
        else:
            print("未能登入, 跳過登出步驟。")
    except Exception as e:
        print(f"自動化腳本執行過程中發生錯誤: {e}")
    finally:
        if driver:
            print("關閉瀏覽器。")
            driver.quit()

if __name__ == "__main__":
    main()



