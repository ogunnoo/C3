import os
import time
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
        # time.sleep(5)
        # d.find_element(By.CSS_SELECTOR, ".pane:nth-child(2) > .btn").click()
    
    return d

def create_cg(logged_in_driver: webdriver.Chrome, group_name: str, location: str):
    """
    Create a new Connect Group in Planning Center Online (PCO) using Selenium WebDriver.

    Args:
        logged_in_driver (webdriver.Chrome): The logged-in Selenium WebDriver instance.
        group_name (str): The name of the group to create.
        location (str): The location for the group.
    Returns:
        webdriver.Chrome: The Selenium WebDriver instance after creating the group.
    """
    # save me
    d = logged_in_driver
    
    ### CREATE CONNECT GROUP ###
    d.implicitly_wait(2)
    # 1 | open | /my_groups | 
    d.get("https://groups.planningcenteronline.com/groups")
    d.implicitly_wait(10)
    # 4 | click | xpath=//div[@id='filtered-groups-header']/div/div/div/button[2] | 
    # d.find_element(By.XPATH, "//div[@id=\'filtered-groups-header\']/div/div/div/button[2]").click()
    d.find_element(By.CSS_SELECTOR, 'button[aria-label="Create a new group"]').click()
    # 5 | click | id=group_group_type_id | 
    d.find_element(By.ID, "group_group_type_id").click()
    # d.find_element(By.ID, "selectFilterGroupTypes").click()
    # 6 | select | id=group_group_type_id | label=Connect Groups
    dropdown = d.find_element(By.ID, "group_group_type_id")
    # d.find_element(By.ID, "item-list-0-item-2").click()
    dropdown.find_element(By.XPATH, "//option[. = 'Connect Groups']").click()
    # 7 | click | id=group_name | 
    d.find_element(By.ID, "group_name").click()
    # 8 | type | id=group_name | [TEST] Dev Selenium4
    d.find_element(By.ID, "group_name").send_keys(str(group_name))

    d.find_element(By.XPATH, "//span[contains(.,'Create group')]").click()
    d.implicitly_wait(4)

    ### ENABLE CHAT ###
    # d.find_element(By.XPATH, "(//button[@type=\'button\'])[10]").click()
    # d.find_element(By.LINK_TEXT, "View settings").click()
    d.find_element(By.XPATH, "//a[contains(text(),'View settings')]").click()
    d.implicitly_wait(2)

    d.find_element(By.CSS_SELECTOR, ".btn:nth-child(4)").click()
    d.implicitly_wait(2)

    ### SET LOCATION ###
    dropdown = d.find_element(By.CSS_SELECTOR, ".select--inline")
    dropdown.find_element(By.XPATH, "//option[. = 'Create a new location...']").click()
    d.implicitly_wait(2)

    d.find_element(By.XPATH, "//div[2]/div/div/div/div/div/input").click()
    d.find_element(By.XPATH, "//div[2]/div/div/div/div/div/input").send_keys(str(location))
    d.implicitly_wait(2)

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

def patch_group(pco: PCO, 
                group_id: int, 
                name: str = None,
                tags: int | list = None,
                schedule: str = None):
    """
    Patch a group with new attributes via the PCO API.

    Args:
        pco (PCO): PCO API client.
        group_id (int): The ID of the group to patch.
        name (str, optional): New name for the group. Defaults to None.
        tags (int | list, optional): New tag IDs for the group. Defaults to None.
        schedule (str, optional): New schedule for the group. Defaults to None.
    Returns:
        dict: The response from the API call.
    """
    # create payload
    attributes = {}
    if name:
        attributes['name'] = name
    if schedule:
        attributes['schedule'] = schedule
    if tags:
        attributes['tag_ids'] = tags

    # make API call to update group
    response = pco.patch(f'/groups/v2/groups/{group_id}', payload={"data": {"attributes": attributes}})
    return response

def get_tag_ids(season: str, campus: str, group_type: str, regularity: str):
    """
    Get the tag IDs for a given season, campus, group type, and regularity and return them as a list.

    Args:
        season (str): The season to tag.
        campus (str): The campus to tag.
        group_type (str): The group type to tag.
        regularity (str): The regularity to tag.
    Returns:
        list: A list of tag IDs.
    """
    season_tag = tag_season(season)
    campus_tag = tag_campus(campus)
    group_type_tag = tag_group_type(group_type)
    regularity_tag = tag_regularity(regularity)

    tags = [season_tag, campus_tag, group_type_tag, regularity_tag]
    tags = [tag for tag in tags if tag is not None]
    return tags

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
    assert 'group_name' in df.columns, "group_name column not found in CSV"

    for _, row in df.iterrows():
        driver = logged_in_driver(driver_init)
        driver.implicitly_wait(2)

        group_name = row['group_name'].strip()
        # group_name = "Summer 2025 CG - " + group_name
        location   = row['location'] if 'location' in row else None
        driver = create_cg(driver, group_name, location)
        print(f"Created group: {group_name}")

        # Get mathcing tag IDs for season/campus/group type/regularity
        tags = get_tag_ids (season=row['season'] if 'season' in row else None,
                            campus=row['campus'] if 'campus' in row else None, 
                            group_type=row['group_type'] if 'group_type' in row else None, 
                            regularity=row['regularity'] if 'regularity' in row else None)

        # add Tags (Season, Campus, Group Type, Regularity) and Schedule here
        patch_group(pco, 
                    group_id=get_group_id(pco, group_name), 
                    tags=tags,
                    schedule=row['schedule'] if 'schedule' in row else None,)

        # Add members to group
        leaders = []
        if 'leader' in row:
            leaders.append(row['leader'])
        if 'co-leaders' in row:
            leaders += row['co-leaders'].split(",")

        for leader_name in leaders:
            member_id = find_person(pco, leader_name)
            if member_id:
                add_member(pco, get_group_id(pco, group_name), member_id)
                print(f"Added {leader_name} to {group_name} as leader")
            else:
                print(f"{leader_name} not found")

if __name__ == "__main__":
    cg_path = os.environ["CONNECT_GROUPS_CSV"]
    main(cg_path)