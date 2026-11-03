import time

from DrissionPage import ChromiumPage
from DrissionPage._elements.chromium_element import ChromiumElement  # ruff: ignore[import-private-name]
from DrissionPage.errors import BaseError  # pyright: ignore[reportMissingTypeStubs]

from sdx_dl.sdxlogger import logger

__all__ = ['CloudflareBypasser']


class CloudflareBypasser:
    def __init__(self, driver: ChromiumPage, max_retries: int = 1, log: bool = True):
        self.driver = driver
        self.max_retries = max_retries
        self.log = log

    @staticmethod
    def find_challenge_shadow_root(page: ChromiumPage):
        page.wait.doc_loaded()
        for ele in page.eles('css:body *'):
            shadow = ele.shadow_root
            if shadow is not None:
                return shadow
        return None

    def __search_recursively_shadow_root_with_iframe(self, ele: ChromiumElement) -> ChromiumElement | None:
        try:
            assert ele.shadow_root() is not None
            shadow = ele.shadow_root()
            if shadow and shadow.tag == 'iframe':
                return shadow.child()
            elif shadow:
                children = shadow.children()
                for child in children:
                    if self.__search_recursively_shadow_root_with_iframe(child):
                        return child
        except (TypeError, AssertionError):
            return None
        return None

    def __search_recursively_shadow_root_with_cf_input(self, ele: ChromiumElement) -> ChromiumElement | None:
        try:
            assert ele.shadow_root() is not None
            shadow = ele.shadow_root()
            if shadow and shadow.ele('tag:input'):
                return shadow.ele('tag:input')
            elif shadow:
                result = None
                for child in shadow.children():
                    if self.__search_recursively_shadow_root_with_cf_input(child):
                        result = child
                        break
                if result:
                    return result
        except (TypeError, AssertionError):
            return None
        return None

    def __locate_cf_button(self) -> ChromiumElement | None:
        button = None
        iframe: ChromiumElement | None = None
        shadow_host = self.find_challenge_shadow_root(self.driver)

        try:
            if shadow_host:
                shadow_root = shadow_host()
                if shadow_root:
                    iframe_element = shadow_root.ele('t:iframe', timeout=30)
                    if iframe_element:
                        self._log_message('Found the iframe inside the shadow root!')
                        iframe_body = iframe_element.ele('t:body')
                        if iframe_body:
                            inner_shadow_root = iframe_body.sr
                            assert inner_shadow_root is not None
                            target_element = inner_shadow_root.ele('tag:input')
                            if target_element:
                                self._log_message(f'Found the target element: {target_element.tag} inside the nested shadow root.')
                                button = target_element
        except (TypeError, AssertionError) as e:
            self._log_message(f'Error finding button: {e!s}')
            return None

        if self.is_bypassed():
            return None

        if isinstance(button, ChromiumElement):
            return button
        else:
            # If the button is not found, search it recursively
            self._log_message('Basic search failed. Searching for button recursively.')
            if shadow_host is not None:
                shadow_root = shadow_host()
                if shadow_root is not None:
                    ele = shadow_root.ele('t:iframe', timeout=30)
                    if isinstance(ele, ChromiumElement):
                        iframe = self.__search_recursively_shadow_root_with_iframe(ele)
            if iframe:
                body = iframe('tag:body')
                if body:
                    button = self.__search_recursively_shadow_root_with_cf_input(body)
            else:
                self._log_message('Iframe not found. Button search failed.')
            return button if isinstance(button, ChromiumElement) else None

    def _log_message(self, message: str):
        if self.log:
            logger.debug(message)

    def __click_verification_button(self):
        try:
            if self.is_bypassed():
                return
            button = self.__locate_cf_button()
            if button:
                self._log_message('Verification button found. Attempting to click.')
                button.click()
                return self.driver.wait.load_start()
            else:
                self._log_message('Verification button not found.')
                return False
        except BaseError as e:
            msg = str(e).split('Version:')[0].replace('\n', '')
            self._log_message(f'Error clicking verification button: {msg}')
            return False

    def is_bypassed(self):
        try:
            title = self.driver.title.lower()
            html = self.driver.html.lower()
            return 'just a moment' not in title and 'please complete the captcha' not in html
        except BaseError as e:
            msg = str(e).split('Version:')[0].replace('\n', '')
            self._log_message(f'Error checking page title: {msg}')
            return False

    def __verfication_page(self):
        html = self.driver.html.lower()
        if 'performing security verification' in html or 'verifying...' in html:
            self._log_message('Founded verification page')
        return 'performing security verification' in html or 'verifying...' in html

    def __is_verification_page(self):
        while self.__verfication_page():
            time.sleep(4)

    def bypass(self):
        try:
            try_count = 0

            while not self.is_bypassed() and try_count < self.max_retries:
                self._log_message(f'Attempt {try_count + 1}: Verification page detected. Trying to bypass...')
                if self.__click_verification_button() and self.__verfication_page():
                    self.__is_verification_page()
                time.sleep(2)
                try_count += 1

            if try_count >= self.max_retries and not self.is_bypassed():
                self._log_message('Exceeded maximum retries. Bypass failed.')

            if self.is_bypassed():
                self._log_message('Bypass successful.')
            else:
                self._log_message('Bypass failed.')
        except BaseError as e:
            msg = str(e).split('Version:')[0].replace('\n', '')
            self._log_message(f'Bypass failed: {msg}')
