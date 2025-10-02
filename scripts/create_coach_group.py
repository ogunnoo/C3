import os
from pypco import PCO
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from pco.utils.tags import tag_season, tag_campus, tag_group_type, tag_regularity

def init_driver():
    """
    Initialize the Selenium WebDriver with Chrome and set the window size.
    """
    driver = webdriver.Chrome()
    driver.set_window_size(1200, 1000)
    return driver

def logged_in_driver(d: webdriver.Chrome):
    """
    Login to Planning Center Online (PCO) using Selenium WebDriver.
    """
    # Login steps
    d.get("https://login.planningcenteronline.com/login/new")
    # print(d.find_elements(By.ID, "email"), d.find_elements(By.ID, "password"))
    d.implicitly_wait(2)

    # don't re-login if already logged in
    if len(d.find_elements(By.ID, "email")) > 0 and len(d.find_elements(By.ID, "password")) > 0:
        d.find_element(By.ID, "email").send_keys(os.environ["PCO_EMAIL"]) 
        d.find_element(By.ID, "password").send_keys(os.environ["PCO_PASSWORD"])
        d.find_element(By.NAME, "commit").click()
        # d.find_element(By.CSS_SELECTOR, ".pane:nth-child(2) > .btn").click()
    
    return d

def create_coach_group(logged_in_driver: webdriver.Chrome, group_name: str):
    """
    Create a new Coach Group in Planning Center Online (PCO) using Selenium WebDriver.

    Args:
        logged_in_driver (webdriver.Chrome): The logged-in Selenium WebDriver instance.
        group_name (str): The name of the group to create.
        location (str): The location for the group.
    Returns:
        webdriver.Chrome: The Selenium WebDriver instance after creating the group.
    """
    # save me
    d = logged_in_driver
    
    ### CREATE COACH GROUP ###
    d.implicitly_wait(2)
    # 1 | open | /my_groups | 
    d.get("https://groups.planningcenteronline.com/groups")
    d.implicitly_wait(5)
    # 4 | click | xpath=//div[@id='filtered-groups-header']/div/div/div/button[2] | 
    # d.find_element(By.XPATH, "//div[@id=\'filtered-groups-header\']/div/div/div/button[2]").click()
    d.find_element(By.CSS_SELECTOR, 'button[aria-label="Create a new group"]').click()
    # 5 | click | id=group_group_type_id | 
    d.find_element(By.ID, "group_group_type_id").click()
    # 6 | select | id=group_group_type_id | label=Connect Groups
    dropdown = d.find_element(By.ID, "group_group_type_id")
    dropdown.find_element(By.XPATH, "//option[. = 'Coach Group']").click()
    # 7 | click | id=group_name | 
    d.find_element(By.ID, "group_name").click()
    # 8 | type | id=group_name | [TEST] Dev Selenium4
    d.find_element(By.ID, "group_name").send_keys(str(group_name))

    d.find_element(By.XPATH, "//span[contains(.,'Create group')]").click()
    d.implicitly_wait(4)


    return d

def get_group_id(pco: PCO, group_name: str):
    """
    Get the group ID for a given group name via the PCO API.

    Args:
        pco (PCO): PCO API client.
        group_name (str): The name of the group to search for.
    Returns:
        int: The ID of the group if found, None otherwise.
    """
    try:
        data = pco.get(f'/groups/v2/groups?where[name]={group_name}')
        print(f"Number of groups matching {group_name}: {len(data['data'])}")
        if data['data']:
            group_id = data['data'][0]['id']
            return group_id
        else:
            print(f"No group found with name: {group_name}")
            return
    except Exception as e:
        print(f"Error fetching group ID for {group_name}: {e}")
        return


def find_person(pco: PCO, name: str):
    """
    Find a person by name via the PCO API.

    Args:
        pco (PCO): PCO API client.
        name (str): The name of the person to search for.
    Returns:
        dict: The response from the API call.
    """
    try:
        data = pco.get(f'/people/v2/people?where[search_name]={name}')
        print(f"Number of people matching {name}: {len(data['data'])}")
        if data['data']:
            person_id = data['data'][0]['id']
            return person_id
        else:
            print(f"No person found with name: {name}")
            return
    except Exception as e:
        print(f"Error fetching pers on ID for {name}: {e}")
        return

def add_member(pco: PCO, 
               group_id: int, 
               member_id: int, 
               role: str = "leader"):
    """
    Add members to a group via the PCO API.

    Args:
        pco (PCO): PCO API client.
        group_id (int): The ID of the group to add members to.
        members (list): A list of member IDs to add.
    Returns:
        dict: The response from the API call.
    """
    import datetime as dt
    now_utc = dt.datetime.now(dt.timezone.utc)
    # create payload
    attributes = {
        "person_id": int(member_id),
        "joined_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "role": role
    }
    response = pco.post(f'/groups/v2/groups/{group_id}/memberships', payload={"data": {"attributes": attributes}})
    return response

def main(cg_path: str = None):
    """
    This can be run as a script to create connect groups in PCO.

    Steps:
    1. Initialize the Selenium WebDriver.
    2. Login to PCO.
    3. Create connect group with name, location, and enable chat.
    4. Update group attributes of season, campus, group type, regularity, and schedule.
    5. Add one leader to the group. (for now, only one leader is supported)
    """
    driver_init = init_driver()
    pco = PCO(os.environ["PCO_APP_ID"], os.environ["PCO_API_KEY"])
    
    # Read CSV file of connect groups
    df = pd.read_csv(cg_path)
    assert 'Coach' in df.columns, "Coach column not found in CSV"

    for coach_name in df['Coach'].unique():
        driver = logged_in_driver(driver_init)
        driver.implicitly_wait(2)

        group_name = "Fall 2025 Coach Group - " + coach_name.strip()
        driver = create_coach_group(driver, group_name)
        print(f"Created group: {group_name}")

        df_coach = df[df['Coach'] == coach_name]
        coaches  = df_coach['Coach_Group_Lead_1'].unique().tolist() + df_coach['Coach_Group_Lead_2'].dropna().unique().tolist()
        leaders  = df_coach['Leader'].tolist()
        print(coaches, leaders)


        # Add leader to group
        for coach in coaches:
            member_id = find_person(pco, coach.strip())
            if member_id:
                add_member(pco, get_group_id(pco, group_name), member_id)
                print(f"Added {coach} to {group_name} as leader")
            else:
                print(f"{coach} not found")

        # Add members to group
        for leader in leaders:
            member_id = find_person(pco, leader.strip())
            if member_id:
                add_member(pco, get_group_id(pco, group_name), member_id, role="member")
                print(f"Added {leader} to {group_name} as member")
            else:
                print(f"{leader} not found")

if __name__ == "__main__":
    cg_path = os.environ["COACH_GROUPS_CSV"]
    main(cg_path)