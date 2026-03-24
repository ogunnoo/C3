from pathlib import Path
import re
from typing import Iterable

from playwright.sync_api import Page, sync_playwright, expect, TimeoutError

from .models import GroupRow

AUTH_FILE = Path("playwright/.auth/planningcenter.json")
ARTIFACTS_DIR = Path("artifacts")


GROUP_TYPE_MAP = {
    "Connect Groups": "448862",
    "Coach Group": "448283",
    "Teams": "444317",
    "Leadership Category Groups": "448873",
    "Team Leaders": "449554",
    "Head Coach Group": "503937",
    "Unique Groups": "unique",
}


def safe_filename(name: str, max_len: int = 80) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:max_len]


def take_failure_screenshot(page: Page, name: str) -> None:
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    safe_name = safe_filename(name)

    try:
        page.screenshot(
            path=str(ARTIFACTS_DIR / f"{safe_name}.png"),
            full_page=True,
            timeout=5000,
        )
    except Exception as exc:
        print(f"Screenshot failed for {name}: {exc}")

    try:
        (ARTIFACTS_DIR / f"{safe_name}.html").write_text(page.content(), encoding="utf-8")
        (ARTIFACTS_DIR / f"{safe_name}.txt").write_text(
            f"URL: {page.url}\nTitle: {page.title()}\n",
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"Debug dump failed for {name}: {exc}")


def maybe_click(locator, timeout: int = 3000) -> bool:
    try:
        expect(locator).to_be_visible(timeout=timeout)
        locator.click()
        return True
    except Exception:
        return False


def goto_groups_home(page: Page) -> None:
    page.goto("https://groups.planningcenteronline.com/", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r"planningcenteronline\.com"), timeout=15000)


def open_create_group(page: Page) -> None:
    button = page.get_by_role("button", name="Create a new group")
    expect(button).to_be_visible(timeout=15000)
    button.click()


def debug_group_type_options(page: Page) -> None:
    options = page.locator("#group_group_type_id option")
    count = options.count()
    print(f"Found {count} group type options:")
    for i in range(count):
        opt = options.nth(i)
        print(
            {
                "text": opt.text_content(),
                "value": opt.get_attribute("value"),
            }
        )


def choose_group_type(page: Page, group_type: str) -> None:
    select = page.locator("#group_group_type_id")
    expect(select).to_be_visible(timeout=10000)

    if group_type in GROUP_TYPE_MAP:
        resolved = GROUP_TYPE_MAP[group_type]
        print(f"Selecting mapped group type value: {resolved}")
        select.select_option(value=resolved)
        return

    try:
        print(f"Trying direct value match: {group_type}")
        select.select_option(value=str(group_type))
        return
    except Exception:
        pass

    print(f"Trying exact label match: {group_type}")
    select.select_option(label=str(group_type))


def create_basic_group(page: Page, row: GroupRow) -> None:
    open_create_group(page)

    name_box = page.get_by_role("textbox", name="Name")
    expect(name_box).to_be_visible(timeout=10000)
    name_box.fill(row.name)

    choose_group_type(page, row.group_type)

    create_button = page.get_by_role("button", name="Create group")
    expect(create_button).to_be_visible(timeout=10000)
    create_button.click()

    page.wait_for_url(re.compile(r"/groups/\d+"), timeout=20000)
    expect(page.get_by_role("button", name="Add a person")).to_be_visible(timeout=20000)

    print("Group creation page loaded")


def debug_after_add_person(page: Page) -> None:
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    (ARTIFACTS_DIR / "add_person_debug.html").write_text(page.content(), encoding="utf-8")


def add_leader(page: Page, leader_name: str) -> None:
    add_person_button = page.get_by_role("button", name="Add a person")
    expect(add_person_button).to_be_visible(timeout=15000)
    add_person_button.click()

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

    expect(add_person_button).to_be_visible(timeout=15000)


def open_settings(page: Page) -> None:
    settings_link = page.get_by_role("link", name="Settings", exact=True)
    expect(settings_link).to_be_visible(timeout=15000)
    settings_link.click()

    # trix-editor is a reliable marker for the settings page in your UI
    expect(page.locator("trix-editor")).to_be_visible(timeout=20000)


def set_chat_to_only_leaders(page: Page) -> None:
    print("Current URL before chat config:", page.url)

    enable_button = page.get_by_role("button", name="Enable chat")
    only_leaders_radio = page.locator("#members_can_create_conversations_no")

    if enable_button.count() > 0 and enable_button.first.is_visible():
        enable_button.click()

    expect(only_leaders_radio).to_be_enabled(timeout=15000)
    only_leaders_radio.check()
    expect(only_leaders_radio).to_be_checked(timeout=10000)


def fill_description(page: Page, description: str) -> None:
    editor = page.locator("trix-editor")
    expect(editor).to_be_visible(timeout=10000)
    editor.click()
    editor.fill(description)

    save_button = page.get_by_role("button", name="Save", exact=True)
    expect(save_button).to_be_visible(timeout=10000)
    save_button.click()


def toggle_checkbox_by_id(page: Page, checkbox_id: str, expected_checked: bool = True) -> None:
    checkbox = page.locator(f"#{checkbox_id}")

    if checkbox.count() == 0:
        print(f"Checkbox not present, skipping: {checkbox_id}")
        return

    expect(checkbox).to_be_attached(timeout=5000)

    try:
        current = checkbox.is_checked()
    except Exception:
        current = bool(checkbox.evaluate("el => !!el.checked"))

    if current == expected_checked:
        print(f"{checkbox_id} already set to {expected_checked}")
        return

    label = page.locator(f'label[for="{checkbox_id}"]')
    if label.count() > 0:
        expect(label.first).to_be_visible(timeout=5000)
        label.first.click()
    else:
        checkbox.evaluate(
            """(el, checked) => {
                el.checked = checked;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            expected_checked,
        )

    if expected_checked:
        expect(checkbox).to_be_checked(timeout=5000)
    else:
        expect(checkbox).not_to_be_checked(timeout=5000)


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
    specific_campuses = page.get_by_text("Specific campuses", exact=True)
    expect(specific_campuses).to_be_visible(timeout=10000)
    specific_campuses.click()

    assign_btn = page.get_by_role("button", name="Assign campus", exact=True)
    expect(assign_btn).to_be_visible(timeout=10000)
    assign_btn.click()

    campus_section = page.locator('[id^="campuses_group_"]').first
    expect(campus_section).to_be_visible(timeout=10000)

    campus_option = campus_section.locator("label", has_text=campus).first
    expect(campus_option).to_be_visible(timeout=10000)
    campus_option.click()

    # Best-effort close if overlay remains open
    page.keyboard.press("Escape")


def assign_tags(page: Page, tags: list[str]) -> None:
    assign_tags_btn = page.get_by_role("button", name="Assign tags", exact=True)
    expect(assign_tags_btn).to_be_visible(timeout=10000)
    assign_tags_btn.click()

    tags_section = page.locator('[id^="tags_group_"]').first
    expect(tags_section).to_be_visible(timeout=10000)

    for tag in tags:
        if not tag:
            continue
        tag_option = tags_section.locator("label", has_text=tag).first
        expect(tag_option).to_be_visible(timeout=10000)
        tag_option.click()

    page.keyboard.press("Escape")


def save_location(page: Page, location_name: str, street_address: str) -> None:
    location_section = page.locator('[id^="location_settings_group_"]').first
    expect(location_section).to_be_visible(timeout=15000)

    location_type = location_section.get_by_role("combobox").first
    expect(location_type).to_be_visible(timeout=10000)
    location_type.select_option(value="new")

    name_box = location_section.get_by_role("textbox").first
    expect(name_box).to_be_visible(timeout=10000)
    name_box.fill(location_name)

    address_box = location_section.get_by_role("textbox", name="Street address")
    expect(address_box).to_be_visible(timeout=10000)
    address_box.fill(street_address)

    # Try to select the autocomplete suggestion.
    suggestion = page.get_by_text(street_address, exact=False).first
    expect(suggestion).to_be_visible(timeout=10000)
    suggestion.click()

    save_button = page.get_by_role("button", name="Save location", exact=True)
    expect(save_button).to_be_visible(timeout=10000)
    save_button.click()


def debug_admin_alert_pairs(page: Page) -> None:
    alert_section = page.locator("section").filter(has_text="Send admin alert if").first
    checkboxes = alert_section.locator('input[type="checkbox"]')
    text_inputs = alert_section.locator('input[type="text"], input[type="number"]')

    print("Admin alert pairs:")
    for i in range(min(checkboxes.count(), text_inputs.count())):
        print(
            {
                "index": i,
                "checkbox_id": checkboxes.nth(i).get_attribute("id"),
                "input_disabled": text_inputs.nth(i).is_disabled(),
            }
        )


def debug_admin_alert_roles(page: Page) -> None:
    alert_section = page.locator("section").filter(has_text="Send admin alert if").first

    print("TEXTBOXES:")
    textbox_count = alert_section.get_by_role("textbox").count()
    for i in range(textbox_count):
        el = alert_section.get_by_role("textbox").nth(i)
        print(
            {
                "index": i,
                "html": el.evaluate("el => el.outerHTML"),
                "text": el.text_content(),
            }
        )

    print("SPINBUTTONS:")
    spin_count = alert_section.get_by_role("spinbutton").count()
    for i in range(spin_count):
        el = alert_section.get_by_role("spinbutton").nth(i)
        print(
            {
                "index": i,
                "html": el.evaluate("el => el.outerHTML"),
                "text": el.text_content(),
            }
        )

    print('EDITABLE ELEMENTS:')
    editable = alert_section.locator('[contenteditable="true"]')
    editable_count = editable.count()
    for i in range(editable_count):
        el = editable.nth(i)
        print(
            {
                "index": i,
                "html": el.evaluate("el => el.outerHTML"),
                "text": el.text_content(),
            }
        )


def debug_admin_alert_labels(page: Page) -> None:
    alert_section = page.locator("section").filter(has_text="Send admin alert if").first
    labels = alert_section.locator("label.checkbox-label")
    for i in range(labels.count()):
        label = labels.nth(i)
        print(
            {
                "index": i,
                "text": label.text_content(),
                "html": label.evaluate("el => el.outerHTML"),
            }
        )


def set_admin_alert(page: Page, days: int) -> None:
    """
    Fill the numeric field associated with:
    'Send admin alert if membership exceeds:'
    Do not click unrelated radio labels in the same section.
    """
    trigger_text = page.get_by_text("Send admin alert if membership exceeds:", exact=False)

    if trigger_text.count() == 0:
        print("Admin alert trigger text not found, skipping.")
        return

    expect(trigger_text.first).to_be_visible(timeout=10000)

    # Find the first non-hidden input after that text in DOM order.
    input_locator = page.locator(
        "xpath=(//*[contains(normalize-space(.), 'Send admin alert if membership exceeds:')])[1]"
        "/following::input[not(@type='hidden')][1]"
    )

    if input_locator.count() == 0:
        print("Admin alert input not found after trigger text, skipping.")
        return

    expect(input_locator.first).to_be_visible(timeout=5000)

    input_type = input_locator.first.get_attribute("type")
    print(f"Admin alert input found. type={input_type!r}")

    # Some UIs render the field readonly/disabled until hydrated; check that first.
    disabled = input_locator.first.is_disabled()
    if disabled:
        print("Admin alert input is disabled, skipping.")
        return

    input_locator.first.fill(str(days))
    expect(input_locator.first).to_have_value(str(days), timeout=5000)
    print(f"Filled admin alert input with: {days}")

def debug_meeting_schedule(page: Page) -> None:
    print("MEETING SCHEDULE COMBOBOXES")
    comboboxes = page.get_by_role("combobox")
    for i in range(comboboxes.count()):
        cb = comboboxes.nth(i)
        try:
            print(
                {
                    "index": i,
                    "enabled": cb.is_enabled(),
                    "html": cb.evaluate("el => el.outerHTML"),
                }
            )
        except Exception as e:
            print({"index": i, "error": str(e)})

    print("LABELLED 'Meets' FIELDS")
    meets = page.get_by_label("Meets")
    for i in range(meets.count()):
        m = meets.nth(i)
        try:
            print(
                {
                    "index": i,
                    "enabled": m.is_enabled(),
                    "html": m.evaluate("el => el.outerHTML"),
                }
            )
        except Exception as e:
            print({"index": i, "error": str(e)})


def debug_schedule_boxes(page: Page) -> None:
    boxes = page.locator('div[role="combobox"]')
    print(f"Schedule combobox count: {boxes.count()}")
    for i in range(boxes.count()):
        box = boxes.nth(i)
        try:
            print(
                {
                    "index": i,
                    "id": box.get_attribute("id"),
                    "html": box.evaluate("el => el.outerHTML"),
                }
            )
        except Exception as e:
            print({"index": i, "error": str(e)})


def select_react_combobox(page: Page, selector: str, value: str) -> None:
    box = page.locator(selector)
    expect(box).to_be_visible(timeout=10000)
    box.click()

    option = page.get_by_role("option", name=value).first
    expect(option).to_be_visible(timeout=10000)
    option.click()
    page.keyboard.press("Enter")  

    # Many react comboboxes close automatically; confirm closed if possible.
    try:
        expect(box).to_have_attribute("aria-expanded", "false", timeout=5000)
    except Exception:
        pass

    expect(box).to_contain_text(value, timeout=5000)


def fill_time_block(container, hour: str | None, minute: str | None, ampm: str | None) -> None:
    container.get_by_role("textbox", name="Hours").fill(hour or "")
    container.get_by_role("textbox", name="Minutes").fill(minute or "")
    container.get_by_role("textbox", name="AM/PM").fill(ampm or "")


def add_meeting_schedule(page: Page, row: GroupRow) -> None:
    add_schedule_link = page.get_by_role("link", name="Add meeting schedule", exact=True)
    expect(add_schedule_link).to_be_visible(timeout=10000)
    add_schedule_link.click()

    frequency_box = "#frequency-name"
    weekday_box = "#frequency-weekday"

    print(f"Target frequency: {row.meeting_frequency}")
    print(f"Target weekday: {row.meeting_day}")

    select_react_combobox(page, frequency_box, row.meeting_frequency)
    select_react_combobox(page, weekday_box, row.meeting_day)

    from_box = page.get_by_label("From", exact=True)
    expect(from_box).to_be_visible(timeout=10000)
    fill_time_block(from_box, row.start_hour, row.start_minute, row.start_ampm)

    to_box = page.get_by_label("to", exact=True)
    expect(to_box).to_be_visible(timeout=10000)
    fill_time_block(to_box, row.end_hour, row.end_minute, row.end_ampm)

    save_button = page.get_by_role("button", name="Save", exact=True)
    expect(save_button).to_be_visible(timeout=10000)
    save_button.click()


def create_group(page: Page, row: GroupRow) -> None:
    create_basic_group(page, row)

    if row.leader_name:
        add_leader(page, row.leader_name)

    open_settings(page)
    set_chat_to_only_leaders(page)

    if row.description:
        fill_description(page, row.description)

    try:
        toggle_visibility_options(page)
    except Exception as exc:
        print(f"Skipping visibility toggles for {row.name}: {exc}")

    if row.campus:
        assign_campus(page, row.campus)

    tags = [t for t in [row.tag_1, row.tag_2] if t]
    if tags:
        assign_tags(page, tags)

    if row.location_name and row.street_address:
        save_location(page, row.location_name, row.street_address)

    if row.admin_alert_days is not None:
        try:
            set_admin_alert(page, row.admin_alert_days)
        except Exception as exc:
            print(f"Skipping admin alert for {row.name}: {exc}")

    if row.meeting_frequency and row.meeting_day:
        add_meeting_schedule(page, row)

    groups_link = page.get_by_role("link", name="Groups", exact=True)
    expect(groups_link).to_be_visible(timeout=10000)
    groups_link.click()

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