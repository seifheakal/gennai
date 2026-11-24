"""Log in through a site's own login form. `login` is also embedded in the generated conftest.

The credentials come from the environment (.env) and are never logged, written to output
files or sent to the LLM. Only the login URL is written into the generated tests.
"""


class LoginFailed(Exception):
    """The login form was submitted but the browser stayed on it."""


def login(page, url, user, password, timeout_ms):
    """Fill the first visible password field and the first text/email field of its form,
    press Enter, and wait until no password field is left on the page."""
    page.goto(url, wait_until="load", timeout=timeout_ms)
    start = page.url.split("#")[0]  # after any redirect
    pw = page.locator("input[type=password]:visible").first
    if pw.count() == 0:
        raise LoginFailed(f"no password field on {url}")
    form = pw.locator("xpath=ancestor::form[1]")
    scope = form if form.count() else page
    fields = "input[type=email]:visible, input[type=text]:visible, input:not([type]):visible"
    scope.locator(fields).first.fill(user)
    pw.fill(password)
    pw.press("Enter")
    for _ in range(max(1, timeout_ms // 100)):
        page.wait_for_timeout(100)
        if page.url.split("#")[0] != start or not pw.is_visible():
            page.wait_for_load_state("load")
            if page.locator("input[type=password]:visible").count() == 0:
                return
    raise LoginFailed(f"still on the login form after submitting it ({page.url})")
