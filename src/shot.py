from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

options = webdriver.ChromeOptions()
options.headless = True
driver = webdriver.Chrome(options=options)
# required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
# required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
# driver.set_window_size(required_width, required_height)
driver.get('http://127.0.0.1:8080/2019-05-10/Amazon')
import time; time.sleep(2)
total_width = driver.execute_script("return document.body.offsetWidth")
total_height = driver.execute_script("return document.body.scrollHeight")
driver.set_window_size(total_width, total_height)
body = driver.find_element_by_id('report')
screen = body.screenshot_as_png
