from pathlib import Path
from playwright.sync_api import Page, sync_playwright, TimeoutError
from playwright.sync_api import expect
from .models import GroupRow
import re

AUTH_FILE = Path("playwright/.auth/planningcenter.json")


def take_failure_screenshot(page, name: str) -> None:
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:80]
    Path("artifacts").mkdir(exist_ok=True)

    try:
        page.screenshot(
            path=f"artifacts/{safe_name}.png",
            full_page=False,
            timeout=5000,
        )
    except Exception as exc:
        print(f"Screenshot failed for {name}: {exc}")

    try:
        Path(f"artifacts/{safe_name}.html").write_text(page.content(), encoding="utf-8")
    except Exception as exc:
        print(f"HTML dump failed for {name}: {exc}")


def goto_groups_home(page: Page) -> None:
    page.goto("https://groups.planningcenteronline.com/", wait_until="domcontentloaded")

def open_create_group(page: Page) -> None:
    page.get_by_role("button", name="Create a new group").click()

def debug_group_type_options(page):
    options = page.locator("#group_group_type_id option")
    count = options.count()
    print(f"Found {count} group type options:")
    for i in range(count):
        opt = options.nth(i)
        print({
            "text": opt.text_content(),
            "value": opt.get_attribute("value"),
        })

def choose_group_type(page, group_type: str) -> None:
    select = page.locator("#group_group_type_id")
    select.wait_for(state="visible")

    GROUP_TYPE_MAP = {
        "Connect Groups": "448862",
        "Coach Group": "448283",
        "Teams": "444317",
        "Leadership Category Groups": "448873",
        "Team Leaders": "449554",
        "Head Coach Group": "503937",
        "Unique Groups": "unique",
    }

    if group_type in GROUP_TYPE_MAP:
        resolved = GROUP_TYPE_MAP[group_type]
        print(f"Selecting by mapped value: {resolved}")
        select.select_option(value=resolved)
        return

    # allow raw values like 448862 in CSV too
    print(f"Trying direct value match: {group_type}")
    try:
        select.select_option(value=str(group_type))
        return
    except Exception:
        pass

    print(f"Trying exact label match: {group_type}")
    select.select_option(label=str(group_type))

def create_basic_group(page: Page, row: GroupRow) -> None:
    open_create_group(page)
    page.get_by_role("textbox", name="Name").fill(row.name)
    choose_group_type(page, row.group_type)

    print("About to click Create group")
    page.get_by_role("button", name="Create group").click()
    print("Clicked Create group")

    expect(page.get_by_role("button", name="Add a person")).to_be_visible(timeout=15000)
    print("Group creation page loaded")

def debug_after_add_person(page: Page) -> None:
    html = page.content()
    with open("artifacts/add_person_debug.html", "w", encoding="utf-8") as f:
        f.write(html)

def add_leader(page: Page, leader_name: str) -> None:
    page.get_by_role("button", name="Add a person").click()

    role_picker = page.locator('[id^="select-"] > .tapestry-react-reset').first
    expect(role_picker).to_be_visible(timeout=10000)
    role_picker.click()

    leader_option = page.get_by_text("Add leader", exact=True)
    expect(leader_option).to_be_visible(timeout=10000)
    leader_option.click()

    search_box = page.get_by_role("textbox", name="Search for someone to add...")
    expect(search_box).to_be_visible(timeout=10000)
    search_box.fill(leader_name)

    person_result = page.get_by_role(
        "button",
        name=re.compile(re.escape(leader_name), re.IGNORECASE),
    ).first
    expect(person_result).to_be_visible(timeout=10000)
    person_result.click()

    confirm_button = page.get_by_role(
        "button",
        name=re.compile(r"^Yes,\s*add", re.IGNORECASE),
    )
    expect(confirm_button).to_be_visible(timeout=10000)
    confirm_button.click()

def fill_description(page, description: str) -> None:
    settings_link = page.get_by_role("link", name="Settings", exact=True)
    expect(settings_link).to_be_visible(timeout=10000)
    settings_link.click()

    editor = page.locator("trix-editor")
    expect(editor).to_be_visible(timeout=10000)
    editor.click()
    editor.fill(description)

    save_button = page.get_by_role("button", name="Save", exact=True)
    expect(save_button).to_be_visible(timeout=10000)
    save_button.click()

def toggle_visibility_options(page: Page) -> None:
    for label in [
        "Show leader's name",
        "Show event schedule",
        "Show meeting schedule",
    ]:
        try:
            page.get_by_text(label).click()
        except TimeoutError:
            pass

def assign_campus(page: Page, campus: str) -> None:
    page.get_by_text("Specific campuses", exact=True).click()

    assign_btn = page.get_by_role("button", name="Assign campus", exact=True)
    expect(assign_btn).to_be_visible(timeout=10000)
    assign_btn.click()

    campus_section = page.locator('[id^="campuses_group_"]').first
    expect(campus_section).to_be_visible(timeout=10000)

    campus_option = campus_section.locator("label", has_text=campus).first
    expect(campus_option).to_be_visible(timeout=10000)
    campus_option.click()

    # Close the open dropdown/panel so it stops intercepting clicks.
    assign_btn.press("Escape")

def assign_tags(page: Page, tags: list[str]) -> None:
    assign_tags_btn = page.get_by_role("button", name="Assign tags", exact=True)
    expect(assign_tags_btn).to_be_visible(timeout=10000)
    assign_tags_btn.click()

    tags_section = page.locator('[id^="tags_group_"]').first
    expect(tags_section).to_be_visible(timeout=10000)

    for tag in tags:
        if tag:
            tag_option = tags_section.locator("label", has_text=tag).first
            expect(tag_option).to_be_visible(timeout=10000)
            tag_option.click()

    page.keyboard.press("Escape")

def save_location(page: Page, location_name: str, street_address: str) -> None:
    location_section = page.locator('[id^="location_settings_group_"]').first

    location_section.get_by_role("combobox").select_option(value="new")
    location_section.get_by_role("textbox").first.fill(location_name)
    location_section.get_by_role("textbox", name="Street address").fill(street_address)
    page.get_by_text(street_address, exact=False).first.click()
    page.get_by_role("button", name="Save location", exact=True).click()

def debug_admin_alert_pairs(page: Page) -> None:
    alert_section = page.locator("section").filter(has_text="Send admin alert if").first
    checkboxes = alert_section.locator('input[type="checkbox"]')
    text_inputs = alert_section.locator('input[type="text"]')

    print("Admin alert pairs:")
    for i in range(min(checkboxes.count(), text_inputs.count())):
        print({
            "index": i,
            "checkbox_id": checkboxes.nth(i).get_attribute("id"),
            "input_disabled": text_inputs.nth(i).is_disabled(),
        })
def debug_admin_alert_roles(page: Page) -> None:
    alert_section = page.locator("section").filter(has_text="Send admin alert if").first

    print("TEXTBOXES:")
    textbox_count = alert_section.get_by_role("textbox").count()
    for i in range(textbox_count):
        el = alert_section.get_by_role("textbox").nth(i)
        print({
            "index": i,
            "html": el.evaluate("el => el.outerHTML"),
            "text": el.text_content(),
        })

    print("SPINBUTTONS:")
    spin_count = alert_section.get_by_role("spinbutton").count()
    for i in range(spin_count):
        el = alert_section.get_by_role("spinbutton").nth(i)
        print({
            "index": i,
            "html": el.evaluate("el => el.outerHTML"),
            "text": el.text_content(),
        })

    print("EDITABLE ELEMENTS:")
    editable = alert_section.locator('[contenteditable="true"]')
    editable_count = editable.count()
    for i in range(editable_count):
        el = editable.nth(i)
        print({
            "index": i,
            "html": el.evaluate("el => el.outerHTML"),
            "text": el.text_content(),
        })
def debug_admin_alert_labels(page: Page) -> None:
    alert_section = page.locator("section").filter(has_text="Send admin alert if").first
    labels = alert_section.locator("label.checkbox-label")
    for i in range(labels.count()):
        label = labels.nth(i)
        print({
            "index": i,
            "text": label.text_content(),
            "html": label.evaluate("el => el.outerHTML"),
        })

def set_admin_alert(page: Page, days: int) -> None:
    alert_section = page.locator("section").filter(has_text="Send admin alert if").first
    expect(alert_section).to_be_visible(timeout=10000)

    labels = alert_section.locator("label.checkbox-label")
    textboxes = alert_section.get_by_role("textbox")

    print(f"Admin alert section: {labels.count()} labels, {textboxes.count()} textboxes")

    # label #2 = Send admin alert if membership exceeds:
    labels.nth(2).click()
    page.wait_for_timeout(300)

    for i in range(textboxes.count()):
        textbox = textboxes.nth(i)
        if textbox.is_enabled():
            textbox.fill(str(days))
            print(f"Filled admin alert textbox #{i}")
            return

    raise RuntimeError("Could not find enabled admin alert textbox.")

# def set_admin_alert(page: Page, days: int) -> None:
#     alert_section = page.locator("section").filter(has_text="Send admin alert if").first
#     expect(alert_section).to_be_visible(timeout=10000)

#     labels = alert_section.locator("label.checkbox-label")
#     textboxes = alert_section.get_by_role("textbox")

#     print(f"Admin alert section: {labels.count()} labels, {textboxes.count()} textboxes")

#     for i in range(labels.count()):
#         label = labels.nth(i)

#         # Click the visible label, not the checkbox input.
#         label.click()
#         page.wait_for_timeout(300)

#         for j in range(textboxes.count()):
#             textbox = textboxes.nth(j)
#             if textbox.is_enabled():
#                 textbox.fill(str(days))
#                 print(f"Filled textbox #{j} after clicking label #{i}")
#                 return

#     raise RuntimeError("Could not find an enabled admin alert textbox after clicking labels.")

def debug_meeting_schedule(page: Page) -> None:
    print("MEETING SCHEDULE COMBOBOXES")
    comboboxes = page.get_by_role("combobox")
    for i in range(comboboxes.count()):
        cb = comboboxes.nth(i)
        try:
            print({
                "index": i,
                "enabled": cb.is_enabled(),
                "html": cb.evaluate("el => el.outerHTML"),
            })
        except Exception as e:
            print({"index": i, "error": str(e)})

    print("LABELLED 'Meets' FIELDS")
    meets = page.get_by_label("Meets")
    for i in range(meets.count()):
        m = meets.nth(i)
        try:
            print({
                "index": i,
                "enabled": m.is_enabled(),
                "html": m.evaluate("el => el.outerHTML"),
            })
        except Exception as e:
            print({"index": i, "error": str(e)})

def debug_schedule_boxes(page: Page) -> None:
    boxes = page.locator('div[role="combobox"]')
    print(f"Schedule combobox count: {boxes.count()}")
    for i in range(boxes.count()):
        box = boxes.nth(i)
        try:
            print({
                "index": i,
                "id": box.get_attribute("id"),
                "html": box.evaluate("el => el.outerHTML"),
            })
        except Exception as e:
            print({"index": i, "error": str(e)})

def add_meeting_schedule(page: Page, row) -> None:
    page.get_by_role("link", name="Add meeting schedule", exact=True).click()
    page.wait_for_timeout(500)

    frequency_box = page.locator("#frequency-name")
    expect(frequency_box).to_be_visible(timeout=10000)

    print(f"Target frequency: {row.meeting_frequency}")
    print(f"Target weekday: {row.meeting_day}")

    # Focus frequency box
    frequency_box.click()

    # Current default is Weekly, so move down to Every other week
    if row.meeting_frequency == "Every other week":
        frequency_box.press("ArrowDown")
        frequency_box.press("ArrowDown")
        frequency_box.press("Enter")
    elif row.meeting_frequency == "Daily":
        frequency_box.press("ArrowUp")
        frequency_box.press("Enter")
    else:
        # fallback: type-ahead
        frequency_box.press(row.meeting_frequency[:2])
        frequency_box.press("Enter")

    expect(frequency_box).to_contain_text(row.meeting_frequency, timeout=5000)
    page.wait_for_timeout(300)

    weekday_box = page.locator("#frequency-weekday")
    expect(weekday_box).to_be_visible(timeout=10000)
    weekday_box.click(force=True)

    if row.meeting_day == "Friday":
        # Sunday default -> Friday
        for _ in range(5):
            weekday_box.press("ArrowDown")
        weekday_box.press("Enter")
    else:
        weekday_box.press(row.meeting_day[:2])
        weekday_box.press("Enter")

    expect(weekday_box).to_contain_text(row.meeting_day, timeout=5000)
    page.wait_for_timeout(300)

    from_box = page.get_by_label("From", exact=True)
    from_box.get_by_role("textbox", name="Hours").fill(row.start_hour or "")
    from_box.get_by_role("textbox", name="Minutes").fill(row.start_minute or "")
    from_box.get_by_role("textbox", name="AM/PM").fill(row.start_ampm or "")

    to_box = page.get_by_label("to", exact=True)
    to_box.get_by_role("textbox", name="Hours").fill(row.end_hour or "")
    to_box.get_by_role("textbox", name="Minutes").fill(row.end_minute or "")
    to_box.get_by_role("textbox", name="AM/PM").fill(row.end_ampm or "")

    page.get_by_role("button", name="Save", exact=True).click()

def create_group(page: Page, row: GroupRow) -> None:
    create_basic_group(page, row)

    if row.leader_name:
        add_leader(page, row.leader_name)

    if row.description:
        fill_description(page, row.description)

    toggle_visibility_options(page)

    if row.campus:
        assign_campus(page, row.campus)

    tags = [t for t in [row.tag_1, row.tag_2] if t]
    if tags:
        assign_tags(page, tags)

    if row.location_name and row.street_address:
        save_location(page, row.location_name, row.street_address)

    if row.admin_alert_days is not None:
        set_admin_alert(page, row.admin_alert_days)

    if row.meeting_frequency and row.meeting_day:
        add_meeting_schedule(page, row)

    page.get_by_role("link", name="Groups", exact=True).click()


def run(csv_rows: list[GroupRow], headless: bool = False) -> None:
    if not AUTH_FILE.exists():
        raise FileNotFoundError("Auth state not found. Run auth bootstrap first.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=str(AUTH_FILE))
        page = context.new_page()

        goto_groups_home(page)

        for row in csv_rows:
            try:
                create_group(page, row)
                print(f"Created: {row.name}")
            except Exception as exc:
                print(f"Failed: {row.name} -> {exc}")
                take_failure_screenshot(page, row.name)

        context.close()
        browser.close()