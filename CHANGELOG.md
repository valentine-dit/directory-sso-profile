# Changelog

## Pre-release

### Implemented enhancements
- TT-990  - Update registration journey of individual user
- TT-1566 - Handle overseas busienss enrolment
- TT-1564 - Update registration journey SSO user with Companies House company
- TT-1577 - Move company title under logo on mobile.
- TT-1575 - Update registration journey for Companies House listed company.
- No ticket - Replace custom breadcrumbs with shared component
- TT-1574 - Update registration journey for non Companies House listed company.
- TT-998 - Support multiple non companies house company types
- TT-1574 - Update registration journey for nont Companies House listed company
- TT-1671 - Add radio button help text to company types list
- TT-1672 - Show banner prompting user to provide business or personal details if missing
- TT-1634 - Show success page on companies house enrolment if no started from "start now"
- TT-1632 - Show success page on non companies house enrolment if no started from "start now"
- TT-1636 - please select pick lists tickets include TT-1638, TT-1640,  TT-1636
- No ticket - Increase flake 8 coverage to 120 lines
- TT-1561 - Show different enrolment title depending on user journey
- TT-1560 - Hide individual account interstitial if intent is create a business profile

### Fixed bugs:
- TT-1728 - Not ask personal details to individual upgrading to business profile
- TT-1647 - Correcting long address not displayed correctly on business search page
- No ticket - Upgrade vulnerable django version to django 1.11.22
- TT-1645 - Fix progress indicator changing from long to short list in new session
- No ticket - Upgraded django to 1.11.23 to fix vulnerability
- No ticket - Remove obsolete settings

## [07-17-2019 ](https://github.com/uktrade/directory-ui-supplier/releases/tag/07-17-2019 )
[Full Changelog](https://github.com/uktrade/directory-ui-supplier/compare/2019.06.05...07-17-2019)

### Implemented enhancements

- TT-1607 - Verification Code allow email

## [2019.06.15](https://github.com/uktrade/directory-ui-supplier/releases/tag/2019.06.05)

[Full Changelog](https://github.com/uktrade/directory-ui-supplier/compare/2019.05.16...2019.06.05)

### Implemented enhancements
- [TT-1392] Fixed UI Bugs on ISD profile page
- TT-1468 Rename "Back" to "Back to profile" in the products and services edit screen
- no ticket - Removed the following obsolete feature flags:
    + FEATURE_BUSINESS_PROFILE_ENABLED
    + FEATURE_NEW_HEADER_FOOTER_ENABLED
    + FEATURE_HEADER_SEARCH_ENABLED
    + FEATURE_EXPERTISE_FIELDS_ENABLED
    + FEATURE_NEW_ACCOUNT_JOURNEY_ENABLED
- no ticket - Fall over if redis is not available
- TT-1501 update isd-url view profile url 
- TT-1321-industry-rewording

### Fixed bugs:
- Upgrade django rest framework to fix security vulnerability

## [2019.05.16](https://github.com/uktrade/directory-ui-supplier/releases/tag/2019.05.16)

[Full Changelog](https://github.com/uktrade/directory-ui-supplier/compare/2019.04.08...2019.05.16)

### Implemented enhancements
- Move form choices to [Constants][directory-constants].
- TT-1426 - Show links to public ISD and FAS profiles
- TT-1423 - Improve content on ISD "other" products and services form

### Fixed bugs:
- Upgraded urllib3 to fix [vulnerability](https://nvd.nist.gov/vuln/detail/CVE-2019-11324)
- Removed old references to Docker.
- TT-1271 - Show dropdown arrow on industry expertise input
- TT-1415 - Allow products and services to be cleared
[directory-constants]: https://github.com/uktrade/directory-constants
- TT-1417 - Populate "Other" products and services with keywords
