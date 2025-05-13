from browserforge.fingerprints import Screen
from camoufox.sync_api import Camoufox

os_list = ["windows", "macos", "linux"]
font_list = ["Arial", "Helvetica", "Times New Roman"]
constrains = Screen(max_width=1920, max_height=1080)


with Camoufox(
    os=os_list,
    fonts=font_list,
    screen=constrains,
    humanize=True,
    main_world_eval=True,
    geoip=True,
) as browser:
    page = browser.new_page()
    page.goto(
        "https://accounts.suno.com/sign-in?redirect_url=https%3A%2F%2Fsuno.com%2Fcreate"
    )
    page.wait_for_load_state("load")
    page.click('button:has(img[alt="Sign in with Google"])')
    page.wait_for_timeout(2000)
    page.type('input[type="email"]', "pbNJ1sznC2Gr@gmail.com")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    page.type('input[type="password"]', "&!8G26tlbsgO")
    page.keyboard.press("Enter")
    page.wait_for_timeout(10000)
    page.wait_for_load_state("load")
    page.wait_for_timeout(100000)
    page.mouse.wheel(0, 1000)
    page.type("textarea.custom-textarea:nth-of-type(2)", "test")
    page.click('a span:contains("Create")')
