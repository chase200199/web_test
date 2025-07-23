from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import logging

logging.basicConfig(
    filename = "automation.log",
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

WEB_UI_LOGIN_URL = "http://192.168.123.85"

PASSWORD = "admin"

CHROMEDRIVER_PATH = './chromedriver.exe'

FIRMWARE_FILE_PATH = './Thecus_x86_64_FW.2.06.02.10_build9703'

ADMIN_ICON_LOCATOR = (By.XPATH, '//*[@id="img_admin"]')
POPUP_PASSWORD_FIELD_LOCATOR = (By.XPATH, '//*[@id="pwd"]')
POPUP_LOGIN_BUTTON_LOCATOR = (By.XPATH, '//*[@id="login_bt"]')
SUCCESS_LOGIN_INDICATOR = (By.XPATH, '//*[@id="33"]')
INVALID_PASSWORD_POPUP_LOCATOR = (By.XPATH, '//*[contains(text(), "Invalid Password")]')
INVALID_PASSWORD_OK_BUTTON_LOCATOR = (By.XPATH, '//*[@id="ext-comp-1002"]')
SYSTEM_MANAGEMENT_MENU_LOCATOR = (By.XPATH, '//*[@id="ext-gen53"]/table/tbody/tr/td[2]')
FIRMWARE_UPGRADE_LOCATOR = (By.XPATH, '//*[@id="ext-gen107"]/div/li[3]/div')
FILE_UPLOAD_INPUT_LOCATOR = (By.XPATH, '//*[@id="UpgradeUploadFile-file"]')
APPLY_BUTTON_LOCATOR = (By.XPATH, '//*[@id="ext-gen341"]')
UPGRADE_POPUP_NEXT1_BUTTON_LOCATOR = (By.XPATH, '//*[@id="ext-gen430"]')
UPGRADE_POPUP_NEXT2_BUTTON_LOCATOR = (By.XPATH, '//*[@id="ext-gen430"]')
PROGRESS_BAR_LOCATOR = (By.XPATH, '//*[@id="ext-gen597"]')
CONTINUE_LOCATOR = (By.XPATH, '//*[@id="ext-gen448"]')
REBOOT_BUTTON_LOCATOR = (By.XPATH, '//*[@id="ext-gen766"]')
REBOOT_CONFIRM_YES_LOCATOR = (By.XPATH, '//*[@id="ext-gen923"]')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=CHROMEDRIVER_PATH)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def login_web_ui(driver, url, password, admin_icon_locator, pass_locator, login_btn_locator, success_indicator_locator, invalid_popup_locator, invalid_popup_ok_btn_locator):
    logger.info(f"導航到登入頁面: {url}")
    driver.get(url)

    try:
        logger.info("等待並點擊 'Admin' 圖示...")
        admin_icon = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(admin_icon_locator)
        )
        admin_icon.click()
        logger.info("'Admin' 圖示已點擊。")

        logger.info("等待彈出框的密碼輸入框出現...")
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(pass_locator)
        )

        logger.info("輸入密碼....")
        password_field.send_keys(password)

        logger.info("等待並點擊彈出框的登入/確認按鈕...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(login_btn_locator)
        )
        login_button.click()

        try:
            logger.info("嘗試判斷登入結果...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(success_indicator_locator)
            )
            logger.info("登入成功!已導向新頁面。")
            time.sleep(3)
            return True
        except TimeoutException:
            logger.info("位在預期時間內導向新頁面, 檢查錯誤彈出框")
            try:
                error_popup = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(invalid_popup_locator)
                )
                logger.warning("偵測到 'Invalid Password' 彈出框!")
                ok_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(invalid_popup_ok_btn_locator)
                )
                ok_button.click()
                logger.info("已點擊彈出框的OK按鈕。")
                driver.save_screenshot("login_failed_invalid_password.png")
                logger.error("登入失敗:密碼錯誤。")
                return False
            except TimeoutException:
                logger.error("登入失敗: 未知的登入問題(既沒導向新頁面, 也沒談出錯誤框)。")
                driver.save_screenshot("login_failed_unkown_issue.png")
                return False
    except Exception as e:
        logger.error(f"登入流程發生一般錯誤: {e}", exc_info=True)
        driver.save_screenshot("login_failed_unknown_issue.png")
        return False
    
def upload_firmware(driver, sys_mgmt_locator, fw_upgrade_locator, file_input_locator, apply_btn_locator, next1_btn1_locator, next2_btn_locator, progress_bar_locator, continue_btn_locator, reboot_btn_locator, confirm_yes_locator, firmware_file_path):
    try:
        Logger.info("點擊[Sysmte Management]...")
        sys_mgmt_btn = WebDriverWait(driver,10).until(EC.element_to_be_clickable(sys_mgmt_locator))
        sys_mgmt_btn.click()
        time.sleep(2)

        logger.info("點擊[Firmware Upgrade]... ")
        fw_upgrade_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(fw_upgrade_locator))
        fw_upgrade_btn.click()
        time.sleep(3)

        logger.info(f"上船韌體檔案: {firmware_file_path}")
        file_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located(file_input_locator))
        file_input.send_keys(firmware_file_path)
        time.sleep(5)

        Logger.info("點擊韌體升級彈出窗的第一個[Next]按鈕...")
        next_button1 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(next1_btn1_locator))
        next_button1.click()
        time.sleep(2)

        Logger.info("點擊韌體升級彈出窗的第二個[Next]按鈕...")
        try:
            next_button2 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(next2_btn_locator))
            next_button2.click()
        except TimeoutException:
            logger.warning("第二個[Next]按鈕未出現, 繼續下一步")
            return True
        
        logger.info("等待韌體升級進度條完成...")
        WebDriverWait(driver, 300).until(
            EC.invisibility_of_element_located(progress_bar_locator)
        )
        logger.info("韌體升級進度條已完成。")
        time.sleep(5)

        Logger.info("點擊[Firmware Successfully Upgraded]視窗中的[Continue]按鈕...")
        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(continue_btn_locator))
        continue_button.click()
        time.sleep(5)

        logger.info("點擊[Reboot]按鈕...")
        reboot_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(reboot_btn_locator))
        reboot_button.click()
        time.sleep(2)

        logger.info("點擊[Reboot]確認視窗中的[Yes]按鈕...")
        confirm_yes_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(confirm_yes_locator))
        confirm_yes_button.click() 
        logger.info("[Yes]按鈕已點擊。")
        time.sleep(300)

        return True
    except Exception as e:
        logger.error(f"韌體升級過程中發生錯誤: {e}", exc_info=True)
        driver.save_screenshot("firmware_upgrade_failed.png")
        return False
    

def main():
    driver = None
    try: 
        driver = setup_driver()
        if login_web_ui(driver, WEB_UI_LOGIN_URL, PASSWORD, ADMIN_ICON_LOCATOR, POPUP_PASSWORD_FIELD_LOCATOR, POPUP_LOGIN_BUTTON_LOCATOR, SUCCESS_LOGIN_INDICATOR, INVALID_PASSWORD_POPUP_LOCATOR, INVALID_PASSWORD_OK_BUTTON_LOCATOR):
            upgrade_firmware(driver, SYSTEM_MANAGEMENT_MENU_LOCATOR, FIRMWARE_UPGRADE_LOCATOR, FILE_UPLOAD_INPUT_LOCATOR, APPLY_BUTTON_LOCATOR, UPGRADE_POPUP_NEXT1_BUTTON_LOCATOR, UPGRADE_POPUP_NEXT2_BUTTON_LOCATOR, PROGRESS_BAR_LOCATOR, CONTINUE_LOCATOR, REBOOT_BUTTON_LOCATOR, REBOOT_CONFIRM_YES_LOCATOR, FIRMWARE_FILE_PATH)
        else:
            logger.info("未能登入, 跳過韌體更新步驟。")
    except Exception as e:
        logger.error(f"自動化腳本執行過程中發生錯誤: {e}", exc_info=True)
    finally:
        if driver:
            print("關閉瀏覽器。")
            driver.quit()

if __name__ == "__main__":
    main()



