# Changelog

## Pre-release

### Implemented enhancements
- TT-1828 - Increasing size of address preview field in registration journey
- TT-1199 - Fixing accessibility issues
- TT-2025 - Update success page content
- No ticket - Removed old feature flagged items
- No ticket - upgrade django

### Fixed bugs:
- TT-1817 - Use correct input types for number fields
- TT-1819 - Fix padding on success box
- TT-1947 - Fix pencil icons
- TT-1855 - Handle companies starting with CE
- no ticket - Set message storage backend
- TT-2092 - Do not show "we will contact you" if already verified
- TT-2095 - Non-admin collaborator view
- TT-2089 - fix-leading-0-verification-code
- TT-1727 - Not prompt collaborators to change business type
- TT-2096 - Fix layout problem on enrolment of individual that already has sso profile
- TT-1708 - link user to ingress url on success page
- TT-2095 - Added "remove from business profile" feature for non-admins
- TT-1855 - Fix incorrect company type label on enrolment
- TT-1132 - Improve contrast of breadcrumbs and feedback link
- TT-1132 - Upgrade directory components to fix accessibility bug
- no ticket - upgrade pillow

## [2019.11.20](https://github.com/uktrade/directory-sso-profile/releases/tag/2019.11.20)
[Full Changelog](https://github.com/uktrade/directory-sso-profile/compare/2019.10.30...2019.11.20)

## Hotfix
- TT-2176 - Fix password form remembering old bad password

## [2019.10.30](https://github.com/uktrade/directory-sso-profile/releases/tag/2019.10.30)
[Full Changelog](https://github.com/uktrade/directory-sso-profile/compare/2019.08.14_1...2019.10.30)

### Implemented enhancements
- GTRANSFORM-364 - text changes on page titles
- GTRANSFORM-364 - add descriptive page titles to profile journey templates
- TT-1725 - Send email to company admin when a new user is added to company profile
- TT-1734 - Add second user to already registered company profile
- TT-1733 - Add request for individual verification feature
- TT-1723 - Add collaborator list admin view
- TT-1716 - Support removing collaborators
- TT-1732 - Added context to incomplete business profile banner
- TT-1713 - Allow user to remove themselves from the business profile
- TT-1714 - Allow single collaborator to invite other admin
- TT-1727 - Allow inviting collaborator
- TT-1673 - Handle backfill details after login
- TT-1748 - Collaboration invitee journey
- TT-1642 - Handle incomplete companies house details
- no ticket - Add IDs to relevant elements on CH enrolement success page
- TT-1760 - added user profile update
- TT-1808 - Update directory components to add "no-validate" no cache middleware
- TT-1783 - Remove FAB Urls and Refactor
- TT-1812? - Fix error when saving with no profile
- TT-1813 - Fix Telephone display in personal details
- TT-1822 - Personal details 500 error
- TT-1827 - fix Broken Fab Template - 500 error
- No Ticket - Amend retrieve_profile to send sso_id instead of sso_session_id
- TT-1702 - Add Google Analytics 360 settings for enrolment journey
- TT-1845 - Show message for expired links
- TT-1795 - Display error message to second user in registation journey
- TT-1841 - Email not displayed on invite new admin
- TT-1821 - Change `I can't find my business` link on company's house registration.
- XOT-1120 - Take user back to the ingress url when registering
- TT-1786 - Change 'start now' text on wizard
- no ticket - Replace `DIRECTORY_CONSTANTS_URL_GREAT_INTERNATIONAL` with `DIRECTORY_CONSTANTS_URL_INTERNATIONAL`
- TT-1903 - Removed Editor from change role in admin panel
- TT-1910 - only display collaborators who haven't accepted in the list
- No ticket - upgrade directory-sso-api-client to 6.2.0
- TT-1911 - Remove access to edit business profile for member user

### Fixed bugs:
- TT-1728 - Not ask personal details to individual upgrading to business profile
- No ticket - Remove obsolete settings
- TT-1731 - Fix address error persistence issue when a valid postcode is entered on UI
- TT-1709 - Account creation content change
- No ticket - Handle user has no supplier on profile page
- TT-1806 - do not prompt non companies house users to verify via companies house
- TT-1830 - No longer prompt users with profiles to create a profile
- TT-1824 - Links no longer empty on 500 and 404 page
- TT-1831 - Fix mobile tab padding
- TT-1795 - Fixing second user registration journey
- No Ticket - Amend retrieve_profile to send sso_id instead of sso_session_id
- TT-1827 - fix Broken Fab Template - 500 error
- TT-1816 - Upgrade directory components to fix js in non-chrome
- TT-1840 - Remove errant red line from case study wizard
- TT-1852 - Allow non-companies house company to edit their business details
- TT-1807 - Hide Publish button on admin
- TT-1857 - Companies House fix request manual verification
- TT-1856 - fix persistent is_enroled msg
- TT-1857   - Companies House fix request manual verification
- TT-1797 - correct page titles
- TT-1819 - Fixing missing background image on tooltip on profile about page
- TT-1899 - fix telephone display and correct case on personal details
- TT-1789 - Wizard drops steps on changing business-type
- TT-1904 - admin defaults to invite collaborators 
- TT-1901 - show name in collaborators list 
- TT-1914 - Reinstate missing terms tickbox
- TT-1915 - Fix update profile error if user has no supplier
- TT-1902 - Collaborator Invite UI bug fixes
- TT-1946 - Remove 'downgrade\upgrade to editor' options in admin tools
- TT-1962 - Fixing verification links in user journeys
- TT-1942 - redirect to form_session.ingress_url for exops intent
- TT-2038 - fix admin breadcrumbs

## [2019.08.14_1](https://github.com/uktrade/directory-sso-profile/releases/tag/2019.08.14_1)
[Full Changelog](https://github.com/uktrade/directory-sso-profile/compare/2019.08.14...2019.08.14_1)

## Hotfix
- TT-1853 - 404-guidence-page

## [2019.08.14](https://github.com/uktrade/directory-sso-profile/releases/tag/2019.08.14)
[Full Changelog](https://github.com/uktrade/directory-sso-profile/compare/2019.06.25_2...2019.08.14)

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

- TT-1647 - Correcting long address not displayed correctly on business search page
- TT-1645 - Fix progress indicator changing from long to short list in new session
- No ticket - Upgraded django to 1.11.23 to fix vulnerabilityI

## [07-17-2019 ](https://github.com/uktrade/directory-sso-profile/releases/tag/07-17-2019 )
[Full Changelog](https://github.com/uktrade/directory-sso-profile/compare/2019.06.05...07-17-2019)

### Implemented enhancements

- TT-1607 - Verification Code allow email

## [2019.06.15](https://github.com/uktrade/directory-sso-profile/releases/tag/2019.06.05)

[Full Changelog](https://github.com/uktrade/directory-sso-profile/compare/2019.05.16...2019.06.05)

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

## [2019.05.16](https://github.com/uktrade/directory-sso-profile/releases/tag/2019.05.16)

[Full Changelog](https://github.com/uktrade/directory-sso-profile/compare/2019.04.08...2019.05.16)

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

