from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from google.cloud import vision
import cv2
import time
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless")  # 無頭
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--force-device-scale-factor=0.7")
driver = webdriver.Chrome(options=chrome_options)  # 瀏覽器只被初始化一次
client = vision.ImageAnnotatorClient.from_service_account_json('token.json')

timeout = 120

URL = "https://tixcraft.com"
LOGIN_URL = "https://tixcraft.com/login/facebook"
ticket = "https://tixcraft.com/activity/game/24_jaychou"
link = ""

headers = {
    "x-requested-with": "XMLHttpRequest"
}

driver.get(f"{URL}/order")
button = WebDriverWait(driver, timeout).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-reject-all-handler"]'))
)   
button.click()

def login_test():
    driver.get(f"{URL}/order")
    current_url = driver.current_url
    if "/login" in current_url:  # 如果被重定向到login
        return False
    else:
        return True

def fb_login(email, password):
    try:
        driver.get(LOGIN_URL)

        input_box = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        input_box.send_keys(email)

        input_box = driver.find_element(By.ID, "pass")
        input_box.send_keys(password)

        button = driver.find_element(By.ID, "loginbutton")
        button.click()

        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-label, '的身分繼續')]"))
        )   
        button.click()
        return True
    except Exception as e:
        print(f"Error occurred: {e}")
        return False

def get_date():
    driver.get(ticket)

    element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, "//*[@id='gameList']/table/tbody")))

    rows = element.find_elements(By.TAG_NAME, "tr")

    table_data = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 4:
            first_td = cols[0].text 
            buttons = cols[3].find_elements(By.TAG_NAME, "button")
            if buttons:
                data_href = buttons[0].get_attribute("data-href")
            else:
                data_href = None
            table_data.append((first_td, data_href))

    for data in table_data:
        print(f"第一個 TD: {data[0]}, 第四個 TD 中的 button data-href: {data[1]}")

def waiting(date):
    global link
    response = requests.get(ticket, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find("table", {"class": "table-bordered"})
        if table:
            rows = table.find("tbody").find_all("tr")  # type: ignore
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    time = cols[0].get_text(strip=True)
                    button = cols[3].find("button")
                    if button:
                        link = button.get("data-href")
                        if date in time:
                            print(f"時間: {time}, 連結: {link}")
                            return link
    return None

def select_seat(href, seat): #$6880
    driver.get(href)
    
    # 查找包含 3080 的 <b> 元素
    elements = driver.find_elements(By.XPATH, "//div[@class='zone-label']//b[contains(text(), '6880')]")
    
    if elements:
        # 打印找到的元素文本
        print(f"找到的元素文本: {elements[0].text}")
        
        # 查找該元素後續的 <ul class='area-list'>
        # 從 elements[0] 開始往後查找，並且只找 <ul class="area-list">
        area_list = elements[0].find_element(By.XPATH, "./following::ul[@class='area-list']")
        
        # 找到 area-list 下的 <li> 元素
        li_elements = area_list.find_elements(By.XPATH, "./li")
        
        # 打印所有找到的 <li> 元素
        for li in li_elements:
            try:
                if seat in li.text:
                    print(f"找到的 li 元素: {li.text}")
                    driver.execute_script("arguments[0].scrollIntoView(true);", li)
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(li))
                    li.click()
                    ticket_type()
            except:
                pass
    else:
        print("未找到包含 6880 的元素")

def ticket_type():
    # 查找所有包含 'gridc' 的 <tr> 元素
    global ticket_url
    ticket_url = driver.current_url
    gridc_elements = driver.find_elements(By.XPATH, "//tbody//tr[@class='gridc']")
    
    for gridc in gridc_elements:
        # 查找 <div class='text-bold'>，檢查是否為 '全票 3,080'
        ticket_type_element = gridc.find_element(By.XPATH, ".//div[@class='text-bold']")
        if '全票' in ticket_type_element.text:
            print(f"找到的票種為: {ticket_type_element.text}")

            # 找到對應的 <select> 元素並設置票數為 4
            select_element = gridc.find_element(By.XPATH, ".//select")
            select_obj = Select(select_element)
            select_obj.select_by_value("4")  # 將票數設置為 4
            button = driver.find_element(By.XPATH, '//*[@id="form-ticket-ticket"]/div[3]')
            button.click()
            get_reCAPTCHA()
            break
    else:
        print("未找到符合條件的全票選項")

def get_reCAPTCHA():
    global screenshot_base64
    image_element = driver.find_element(By.XPATH, '//*[@id="TicketForm_verifyCode-image"]')
    image_data = image_element.screenshot_as_png
    vision_image = vision.Image(content=image_data)
    response = client.text_detection(image=vision_image) # type: ignore
    texts = response.text_annotations
    for text in texts:
        txt = text.description
        break

    input_box = driver.find_element(By.XPATH, '//*[@id="TicketForm_verifyCode"]')
    input_box.send_keys(txt.lower().strip().replace(" ", ""))

    button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="form-ticket-ticket"]/div[4]/button[2]'))
    )   
    button.click()

    try:
        current_url = driver.current_url
        if current_url != ticket_url:
            print("run ing")
            wait_for_page_load(driver)
            
            # 查找 class 中包含 'field-CheckoutForm' 的元素
            payment_box = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "paymentBox"))
            )

            # 找到所有 pay-column
            pay_columns = payment_box.find_elements(By.CLASS_NAME, "pay-column")

            for column in pay_columns:
                # 在每個 pay-column 中找到 form-check
                form_check = column.find_element(By.CLASS_NAME, "form-check")
                
                # 找到 label 並檢查是否為 ATM 虛擬帳號付款
                label = form_check.find_element(By.TAG_NAME, "label")
                
                if "ATM虛擬帳號付款" in label.text:
                    # 找到對應的 radio input 並點擊
                    radio_button = form_check.find_element(By.TAG_NAME, "input")
                    driver.execute_script("arguments[0].scrollIntoView(true);", radio_button)
                    radio_button.click()
                    time.sleep(1.5)
                    button = driver.find_element(By.XPATH, '//*[@id="submitButton"]')
                    button.click()
                    element = driver.find_element(By.XPATH, "/html/body/div[2]/div[1]")
                    screenshot_base64 = driver.get_screenshot_as_base64()
                    socketio.emit('Take_Your_Ticket', {'b64': screenshot_base64}) # type: ignore
                    return screenshot_base64
    
    except UnexpectedAlertPresentException:
        try:
            alert = driver.switch_to.alert
            print(f"Alert Text: {alert.text}")
            alert.accept()
            ticket_type()
        except NoAlertPresentException:
            ticket_type()

def wait_for_page_load(driver, timeout = timeout):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )