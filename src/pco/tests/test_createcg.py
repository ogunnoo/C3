import pytest
import os
from selenium import webdriver
from selenium.webdriver.common.by import By

@pytest.fixture(scope="session")
def driver():
  driver = webdriver.Chrome()
  driver.set_window_size(500, 500)
  yield driver
  # driver.quit()

@pytest.fixture
def logged_in_driver(driver):
  # Login steps
  driver.get("https://login.planningcenteronline.com/login/new")
  # print(driver.find_elements(By.ID, "email"), driver.find_elements(By.ID, "password"))
  driver.implicitly_wait(2)

  # don't re-login if already logged in
  if len(driver.find_elements(By.ID, "email")) > 0 and len(driver.find_elements(By.ID, "password")) > 0:
    driver.find_element(By.ID, "email").send_keys(os.environ("PCO_EMAIL")) 
    driver.find_element(By.ID, "password").send_keys(os.environ("PCO_PASSWORD"))
    driver.find_element(By.NAME, "commit").click()
    driver.find_element(By.CSS_SELECTOR, ".pane:nth-child(2) > .btn").click()
  
  yield driver

@pytest.mark.parametrize("group_name", [
  '[TEST] Selenium ABC',
  '[TEST] Selenium BCA',
  '[TEST] Selenium CAB'
])
def test_create_cg(logged_in_driver, group_name):
  driver = logged_in_driver
  
  driver.implicitly_wait(2)
  # 1 | open | /my_groups | 
  driver.get("https://groups.planningcenteronline.com/groups")
  driver.implicitly_wait(5)
  # 4 | click | xpath=//div[@id='filtered-groups-header']/div/div/div/button[2] | 
  driver.find_element(By.XPATH, "//div[@id=\'filtered-groups-header\']/div/div/div/button[2]").click()
  # 5 | click | id=group_group_type_id | 
  driver.find_element(By.ID, "group_group_type_id").click()
  # 6 | select | id=group_group_type_id | label=Connect Groups
  dropdown = driver.find_element(By.ID, "group_group_type_id")
  dropdown.find_element(By.XPATH, "//option[. = 'Connect Groups']").click()
  # 7 | click | id=group_name | 
  driver.find_element(By.ID, "group_name").click()
  # 8 | type | id=group_name | [TEST] Dev Selenium4
  driver.find_element(By.ID, "group_name").send_keys(str(group_name))

  driver.find_element(By.XPATH, "//span[contains(.,'Create group')]").click()
  driver.implicitly_wait(2)