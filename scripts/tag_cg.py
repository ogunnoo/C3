import os
from pypco import PCO
import pandas as pd
from pco.utils.tags import tag_season, tag_campus, tag_group_type, tag_regularity, tag_demographics

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

def get_tag_ids(season: str, campus: str, group_type: str, regularity: str, demographics: str):
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
    demographics_tag = tag_demographics(demographics)

    tags = [season_tag, campus_tag, group_type_tag, regularity_tag, demographics_tag]
    tags = [tag for tag in tags if tag is not None]
    return tags


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
    from tqdm.auto import tqdm
    pco = PCO(os.environ["PCO_APP_ID"], os.environ["PCO_API_KEY"])
    
    # Read CSV file of connect groups
    df = pd.read_csv(cg_path)
    assert 'group_name' in df.columns, "group_name column not found in CSV"

    for _, row in tqdm(df.iterrows()):
        group_name = row['group_name']
        group_name = "Summer 2025 CG - " + group_name
        print(f"Updating group: {group_name}")

        # Get mathcing tag IDs for season/campus/group type/regularity
        tags = get_tag_ids (season=row['season'] if 'season' in row else None,
                            campus=row['campus'] if 'campus' in row else None, 
                            group_type=row['group_type'] if 'group_type' in row else None, 
                            regularity=row['regularity'] if 'regularity' in row else None,
                            demographics=row['demographic'] if 'demographic' in row else None)

        # add Tags (Season, Campus, Group Type, Regularity) and Schedule here
        patch_group(pco, 
                    group_id=get_group_id(pco, group_name), 
                    tags=tags,)
                    # schedule=row['schedule'] if 'schedule' in row else None,)


if __name__ == "__main__":
    cg_path = os.environ["CONNECT_GROUPS_CSV"]
    main(cg_path)