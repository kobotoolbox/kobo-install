# White-Label Refactor Changelog

## [Phase 1] - Initial Refactor (2026-03-16)

### Added
- Centralized branding variables in `helpers/config.py`:
  - `app_name`: Brand name of the platform.
  - `app_support_email`: Contact email for support.
  - `app_default_from_email`: Default sender for notifications.
- Interactive branding questions during the initial setup (`--setup`).
- Support for `APP_NAME`, `APP_SUPPORT_EMAIL`, and `APP_DEFAULT_FROM_EMAIL` in the template rendering engine (`helpers/template.py`).

### Modified
- `run.py`: Welcome message now uses the configured `app_name`.
- `helpers/cli.py`: Automated replacement of "KoboToolbox" with `app_name` in all CLI output (colored print/input).
- `templates/kobo-env/envfiles/django.txt.tpl`: `KOBO_SUPPORT_EMAIL` now uses `APP_SUPPORT_EMAIL`.
- `templates/kobo-env/envfiles/smtp.txt.tpl`: `DEFAULT_FROM_EMAIL` now uses `APP_DEFAULT_FROM_EMAIL`.

### Security Note
- Internal Docker service names and networking remain untouched to preserve compatibility and prevent breakage in established environments.
- All secrets generation (Django, Enketo) remains unchanged.

---
*Developed by Antigravity AI for kobo-install fork.*
