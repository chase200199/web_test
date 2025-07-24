from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, NoAlertPresentException
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
PASSWORD = "admin"
CHROMEDRIVER_PATH = './chromedriver.exe'
FIRMWARE_FILE_PATH = 'C:\\Users\\Chase\\Desktop\\WEB_auto_test\\rom.ima'

# --- UI登入定位器 ---
USERNAME_FIELD_LOCATOR = (By.ID, "userid")
PASSWORD_FIELD_LOCATOR = (By.ID, "password")
LOGIN_BUTTON_LOCATOR = (By.ID, "btn-login")

# --- 一般載入指示器 ---
LOADING_SPINNER_LOCATOR = (By.ID, "processing_layout")

# --- 韌體更新定位器 ---
MAINTENANCE_MENU_LOCATOR = (By.XPATH, "//a[@href='#maintenance' and .//span[text()='維護']]")
FIRMWARE_UPDATE_BUTTON_LOCATOR = (By.XPATH, "//a[@href='#maintenance/firmware_update_wizard' and .//span[text()='韌體更新']]")
CHOOSE_FILE_INPUT_LOCATOR = (By.ID, "mainfirmware_image")
START_UPLOAD_BUTTON_LOCATOR = (By.ID, "btnFirmwareChecks")
FIRMWARE_IMAGE_DROPDOWN_LOCATOR = (By.ID, "idimage_update")
CONFIRM_UPDATE_BUTTON_LOCATOR = (By.ID, "start")
FLASH_SELECTED_BLOCK_BUTTON_LOCATOR = (By.ID, "start")

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

def handle_browser_confirm_dialog(driver, timeout=5):
    """
    處理瀏覽器的確認對話框
    """
    try:
        alert = WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert_text = alert.text
        logger.info(f"偵測到瀏覽器確認對話框, 內容: '{alert_text}'。點擊[確定]。")
        alert.accept()  # 接受對話框
        logger.info("瀏覽器對話框已經接受。")
        return True
    except TimeoutException:
        logger.warning(f"在 {timeout} 秒內未偵測到瀏覽器對話確認框。")
        return False
    except NoAlertPresentException:
        logger.warning("嘗試切換到Alert時, 沒有Alert存在")
        return False
    except Exception as e:
        logger.error(f"處理確認對話框時發生錯誤: {e}", exc_info=True)
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
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(password_locator)
        ) #直接嘗試尋找
        logger.info("輸入密碼....")
        password_field.send_keys(password)

        logger.info("嘗試尋找並點擊[登入]按鈕...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(login_btn_locator)
        ) #直接嘗試尋找
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

def perform_firmware_update(driver, maintenance_menu_locator, firmware_update_button_locator,
                            choose_file_input_locator, firmware_file_path, start_upload_button_locator,
                            firmware_image_dropdown_locator, confirm_update_button_locator,
                            flash_selected_block_button_locator, loading_spinner_locator):
    """
    導航到韌體更新區塊, 上傳韌體, 並開始更新
    """
    logger.info("--- 開始韌體更新流程 ---")
    try:
        # 1. 點擊左側面板的[維護]
        logger.info(f"點擊維護選單: {maintenance_menu_locator}")
        maintenance_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(maintenance_menu_locator)
        )
        maintenance_menu.click()
        logger.info("[維護]選單已點擊...")

        # 2. 等待[處理中]消失
        logger.info("點擊[維護]選單後等待載入指示器...")
        if not wait_for_loading_spinner(driver, loading_spinner_locator):
            logger.error("韌體更新頁面載入超時。")
            return False
        # 3. 尋找並點擊韌體更新按鈕 
        logger.info(f"點擊韌體更新按鈕: {firmware_update_button_locator}")
        firmware_update_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(firmware_update_button_locator)
        )
        firmware_update_button.click()
        logger.info("[韌體更新]按鈕已點擊。")
        time.sleep(2)  # 等待頁面穩定

        # 4. 等待UI重定向並找到[選擇檔案]輸入框
        logger.info("等待韌體上傳頁面載入且[選擇檔案]輸入框出現。")
        choose_file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(choose_file_input_locator)
        )
        if not os.path.exists(firmware_file_path):
            logger.error(f"未在指定路徑找到韌體檔案: {firmware_file_path}")
            return False
        
        logger.info(f"上傳韌體檔案: {firmware_file_path}")
        choose_file_input.send_keys(firmware_file_path)
        logger.info("韌體檔案以選取(透過send_keys方式)。")

        # 5. 點擊[開始韌體更新]按鈕(檔案上傳後的第一個按鈕)

        logger.info(f"嘗試點擊檔案上傳後的第一個[開始韌體更新]按鈕: {start_upload_button_locator}")
        start_upload_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(start_upload_button_locator)
        )
        start_upload_button.click()
        logger.info("檔案上傳後的第一個[開始韌體更新]按鈕已點擊。")
        # 6. 點擊[開始韌體更新]後, 會有一個載入指示器, 等待其消失
        logger.info("等待上傳後載入指示器出現並消失。")
        if not wait_for_loading_spinner(driver, LOADING_SPINNER_LOCATOR, timeout_appear=30, timeout_disappear=120):
            logger.error("韌體上傳過程中載入指示器超時。")
            return False

        # 7. 載入指示器消失後, 會出現下拉選單, 選擇(映像檔1)
        logger.info(f"等待韌體映像檔下拉選單出現: {firmware_image_dropdown_locator}")
        image_dropdown_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(firmware_image_dropdown_locator)
        )
        image_dropdown = Select(image_dropdown_element)
        logger.info("選擇下拉選單中的(映像檔1)。")
        image_dropdown.select_by_visible_text("映像檔1")
        time.sleep(1)  

        # 8. 選擇映像檔後, 點擊下方[開始韌體更新]    
        logger.info(f"點擊下方[開始韌體更新]按鈕: {confirm_update_button_locator}")
        final_update_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(confirm_update_button_locator)
        )
        final_update_button.click()
        logger.info("[開始韌體更新]按鈕已點擊。")

        # 9. 處理彈出確認視窗(瀏覽器confirm dialog)
        logger.info("檢查瀏覽器內建確認對話框。")
        if not handle_browser_confirm_dialog(driver, timeout=5):
            logger.error("韌體更新確認對話框未能處理。")
            return False
        
        # 10. 等待韌體更新時的載入指示器消失
        logger.info("韌體更新確認步驟完成, 等待最終的載入指示器")
        if not wait_for_loading_spinner(driver, LOADING_SPINNER_LOCATOR, timeout_appear=30, timeout_disappear=600):
            logger.error("最終韌體更新載入指示器超時。更新可能仍在進行中或以失敗。")
            return False
        # 11. 等待[所選取的區段進行Flash]按鈕出現並點擊
        logger.info(f"等待[所選取的區段進行Flash]按鈕出現: {flash_selected_block_button_locator}")
        flash_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(flash_selected_block_button_locator)
        )
        flash_button.click()
        logger.info("[所選取的區段進行Flash]按鈕已點擊。")
        if not handle_browser_confirm_dialog(driver, timeout=5):
            logger.error("未能處理所選取區段進行Flash的跳出視窗。韌體更新程序中止。")
            return False
        # 12. 等待載入指示器出現並消失
        logger.info("等待[所選取的區段flash]之後的載入指示器出現並消失。")
        if not wait_for_loading_spinner(driver, loading_spinner_locator, timeout_appear=30, timeout_disappear=600):
            logger.error("韌體更新過程中載入指示器超時。")
            return False
        
        # 13. 最後一個瀏覽器對話確認框顯示
        logger.info("等待最後一個瀏覽器對話確認框出現並點擊確認")
        if not handle_browser_confirm_dialog(driver, timeout=5):
            logger.error("韌體更新過程中未能處理最後的瀏覽器對話確認框。")
            return False
        
        logger.info("韌體更新流程已成功完成。")
        return True
    
    except TimeoutException:
        logger.error("韌體更新過程中等待元素超時。", exc_info=True)
        return False
    except NoSuchElementException:
        logger.error("韌體更新過程中未找到必要元素。", exc_info=True)
        return False
    except WebDriverException as e:
        logger.error(f"WebDriver錯誤: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"韌體更新過程中發生未預期錯誤: {e}", exc_info=True)
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
            logger.info("登入成功。繼續韌體更新。")

            if perform_firmware_update(
                driver, MAINTENANCE_MENU_LOCATOR, FIRMWARE_UPDATE_BUTTON_LOCATOR,
                CHOOSE_FILE_INPUT_LOCATOR, FIRMWARE_FILE_PATH, START_UPLOAD_BUTTON_LOCATOR,
                FIRMWARE_IMAGE_DROPDOWN_LOCATOR, CONFIRM_UPDATE_BUTTON_LOCATOR,
                FLASH_SELECTED_BLOCK_BUTTON_LOCATOR, LOADING_SPINNER_LOCATOR
            ):
                logger.info("韌體更新流程已成功完成。")
            else:
                logger.error("韌體更新流程失敗。") 
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



