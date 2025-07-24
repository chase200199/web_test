from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import os
import logging

logging.basicConfig(
    filename = "lom_automation.log",
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- 設定 ---
WEB_UI_LOGIN_URL_HTTPS = "https://192.168.122.33"
USERNAME = "admin"
PASSWORD = "12345678"
CHROMEDRIVER_PATH = './chromedriver.exe'
FIRMWARE_FILE_PATH = 'C:\\Users\\Chase\\Desktop\\WEB_auto_test\\enc_rom_ima_enc'

# --- 定位器 ---
USERNAME_FIELD_LOCATOR = (By.ID, "userid")
PASSWORD_FIELD_LOCATOR = (By.ID, "password")
LOGIN_BUTTON_LOCATOR = (By.ID, "btn-login")

# --- 一般載入指示器 ---
LOADING_SPINNER_LOCATOR = (By.ID, "processing_layout")

# --- 輔助函數 ---
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    #忽略SSL錯誤
    chrome_options.add_argument("--ignore-certificate-errors")

    service = Service(executable_path=CHROMEDRIVER_PATH)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver
def wait_for_loading_spinner(driver, spinner_locator, timeout_appear=30, timeout_disappear=60):
    """
    等待載入指示器出現並消失
    用於處理頁面載入和使用者介面更新
    """
    try:
        logger.info(f"等待載入指示器出現 (ID: {spinner_locator[1]})...")
        #判斷是否可見
        WebDriverWait(driver, timeout_appear).until(EC.visibility_of_element_located(spinner_locator))
        logger.info("載入指示器已出現, 等待其消失...")
        WebDriverWait(driver, timeout_disappear).until(EC.invisibility_of_element_located(spinner_locator))
        logger.info("載入指示器已消失。")
        return True
    except TimeoutException:
        logger.error("等待載入指示器未在預期時間內消失。頁面可能載入緩慢或卡住。")
        return False
    except Exception as e:
        logger.error(f"等待載入指示器時發生錯誤: {e}", exc_info=True)
        return False

# --- 核心函數 ---
def perform_login(driver, url, username, password, username_locator, password_locator, login_btn_locator, loading_spinner_locator):
    """
    執行登入操作, 包括使用者名稱/密碼輸入和登入按鈕點擊, 並且載入指示器
    """
    logger.info(f"導航到登入頁面: {url}")
    driver.get(url)

    try:
        logger.info("等待使用者名稱輸入欄位出現...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(username_locator)
        )
        logger.info(f"輸入使用者名稱: {username}")
        username_field.send_keys(username)

        logger.info("嘗試尋找密碼輸入欄位並輸入...")
        password_field = driver.find_element(*password_locator) #直接嘗試尋找
        logger.info("輸入密碼....")
        password_field.send_keys(password)

        logger.info("嘗試尋找並點擊[登入]按鈕...")
        login_button = driver.find_element(*login_btn_locator) #直接嘗試尋找
        login_button.click()
        logger.info("[登入]按鈕已點擊...")

        # 登入後, 使用者介面可能會顯示第一個載入指示器
        if not wait_for_loading_spinner(driver, loading_spinner_locator):
            logger.error("登入後第一個載入指示器超時。")
            return False
        
        time.sleep(2)  # 給一點時間緩衝, 等待頁面穩定
        logger.info("等待新頁面載入後的第二個載入指示器")
        if not wait_for_loading_spinner(driver, loading_spinner_locator):
            logger.error("新頁面載入時的第二個載入指示器超時。")
            return False

        logger.info("登入成功且頁面已準備就緒...")
        return True
    except Exception as e:
        logger.error(f"登入過程中發生錯誤: {e}", exc_info=True)
        return False
    
# --- 主要執行區塊 ---
def main():
    driver = None
    try: 
        driver = setup_driver()
        # 執行登入流程
        if perform_login(driver, WEB_UI_LOGIN_URL_HTTPS, USERNAME, PASSWORD,
                         USERNAME_FIELD_LOCATOR, PASSWORD_FIELD_LOCATOR,
                         LOGIN_BUTTON_LOCATOR, LOADING_SPINNER_LOCATOR):
            logger.info("登入成功...")
        else:
            logger.error("登入失敗, 腳本終止。")
    except Exception as e:
        logger.error(f"腳本執行過程中發生錯誤: {e}", exc_info=True)
    finally:
        if driver:
            logger.info("關閉瀏覽器...")
            driver.quit()

if __name__ == "__main__":
    main()



