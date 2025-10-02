"""
Dear reader:
I know this is super ugly and not the best way to do this, 
but NEXT TIME we will refactor this via YAML or match via the groups/tag_ids API.
"""

def tag_demographics(demographics: str):
    match demographics:
        case "Men":
            return 1992370
        case "Women":
            return 1992371
        case "Mixed":
            return 1992372


def tag_group_type(group_type: str):
    match group_type:
        case "Sermon-based":
            return 1992369
        case "Activity-based (with sermon discussion)":
            return 541206
        case "How to Read the Bible":
            return 541205
        case "Finding Freedom":
            return 1987210
        case "Alpha (New Christians)":
            return 1987211
        case "Alpha Pre Marriage":
            return 1987212
        case "Alpha Marriage":
            return 1987213
        case "Love This City":
            return 1987214
        case "Coaches":
            return 2007847
        case "Head Coaches":
            return 2007848
    return

def tag_campus(campus: str):
    match campus:
        case "Midtown":
            return 541210
        case "Hamilton":
            return 541211
        case "Downtown":
            return 541212
    return

def tag_season(season: str):
    match season:
        case "Fall 2024":
            return 541216
        case "Winter":
            return 2007585 #winter 2025
        case "Summer":
            return 2007586 #summer 2025
        case "Fall":
            return 2007587 #fall 2025
    return

def tag_regularity(regularity: str):
    match regularity:
        case "Weekly":
            return 541217
        case "Bi Weekly":
            return 541219
    return