import time
from DrissionPage import ChromiumPage
from DrissionPage._elements.chromium_element import ChromiumElement
from sdx_dl.sdxlogger import logger

__all__ = ["CloudflareBypasser"]


class CloudflareBypasser:
    def __init__(self, driver: ChromiumPage, max_retries: int = 1, log: bool = True):
        self.driver = driver
        self.max_retries = max_retries
        self.log = log

    def search_recursively_shadow_root_with_iframe(self, ele: ChromiumElement) -> ChromiumElement | None:
        shadow = ele.shadow_root()
        if shadow and shadow.tag == "iframe":
            return shadow.child()
        elif shadow:
            children = shadow.children()
            for child in children:
                if self.search_recursively_shadow_root_with_iframe(child):
                    return child

        return None

    def search_recursively_shadow_root_with_cf_input(self, ele: ChromiumElement) -> ChromiumElement | None:
        shadow = ele.shadow_root()
        if shadow and shadow.ele("tag:input"):
            return shadow.ele("tag:input")
        elif shadow:
            result = None
            for child in shadow.children():
                if self.search_recursively_shadow_root_with_cf_input(child):
                    result = child
                    break
            if result:
                return result

        return None

    def locate_cf_button(self) -> ChromiumElement | None:
        button: ChromiumElement | None = None
        iframe: ChromiumElement | None = None
        eles = self.driver.eles("tag:input")
        for ele in eles:
            if "name" in ele.attrs.keys() and "type" in ele.attrs.keys():
                if "turnstile" in ele.attrs["name"] and ele.attrs["type"] == "hidden":
                    button = ele.parent().shadow_root.child()("tag:body").shadow_root("tag:input")  # type: ignore
                    break

        if isinstance(button, ChromiumElement):
            return button
        else:
            # If the button is not found, search it recursively
            self.log_message("Basic search failed. Searching for button recursively.")
            ele = self.driver.ele("tag:body")
            iframe = self.search_recursively_shadow_root_with_iframe(ele)  # type: ignore
            if iframe:
                body = iframe("tag:body")
                if body:
                    button = self.search_recursively_shadow_root_with_cf_input(body)
            else:
                self.log_message("Iframe not found. Button search failed.")
            return button if isinstance(button, ChromiumElement) else None

    def log_message(self, message: str):
        if self.log:
            logger.debug(message)

    def click_verification_button(self):
        try:
            button = self.locate_cf_button()
            if isinstance(button, ChromiumElement):
                self.log_message("Verification button found. Attempting to click.")
                button.click()
            else:
                self.log_message("Verification button not found.")

        except Exception as e:
            msg = e.__str__().split('Version:')[0].replace('\n', '')
            self.log_message(f"Error clicking verification button: {msg}")

    def is_bypassed(self):
        try:
            title = self.driver.title.lower()
            html = self.driver.html.lower()
            return "just a moment" not in title and "please complete the captcha" not in html
        except Exception as e:
            msg = e.__str__().split('Version:')[0].replace('\n', '')
            self.log_message(f"Error checking page title: {msg}")
            return False

    def bypass(self):
        try:
            try_count = 0

            while not self.is_bypassed() and try_count < self.max_retries:
                self.log_message(f"Attempt {try_count + 1}: Verification page detected. Trying to bypass...")
                self.click_verification_button()

                try_count += 1
                time.sleep(4)

            if try_count >= self.max_retries and not self.is_bypassed():
                self.log_message("Exceeded maximum retries. Bypass failed.")

            if self.is_bypassed():
                self.log_message("Bypass successful.")
            else:
                self.log_message("Bypass failed.")
        except Exception as e:
            msg = e.__str__().split('Version:')[0].replace('\n', '')
            self.log_message(f'Bypass failed: {msg}')
