# directory-sso-profile

[![code-climate-image]][code-climate]
[![circle-ci-image]][circle-ci]
[![codecov-image]][codecov]
[![gitflow-image]][gitflow]
[![calver-image]][calver]

---

**SSO Profile - the Department for International Trade (DIT) service for managing EIG profiles.**

### See also:
| [directory-api](https://github.com/uktrade/directory-api) | [directory-ui-buyer](https://github.com/uktrade/directory-ui-buyer) | [directory-ui-supplier](https://github.com/uktrade/directory-ui-supplier) | [directory-ui-export-readiness](https://github.com/uktrade/directory-ui-export-readiness) |
| --- | --- | --- | --- |
| **[directory-sso](https://github.com/uktrade/directory-sso)** | **[directory-sso-proxy](https://github.com/uktrade/directory-sso-proxy)** | **[directory-sso-profile](https://github.com/uktrade/directory-sso-profile)** |  |

For more information on installation please check the [Developers Onboarding Checklist](https://uktrade.atlassian.net/wiki/spaces/ED/pages/32243946/Developers+onboarding+checklist)

## Development

The back-end framework is Django 1.9. The front-end uses minimal Javascript. The motivation for this is for accessibility reasons, to reduce technical complexity, and reduce cross-browser compatibility issues. Therefore most front-end work will be HTML and SASS/CSS development.

We aim to follow [GDS service standards](https://www.gov.uk/service-manual/service-standard) and [GDS design principles](https://www.gov.uk/design-principles).

## Requirements
[Python 3.6](https://www.python.org/downloads/release/python-366/)

[Redis]( https://redis.io/)

### SASS
We use SASS CSS pre-compiler. If you're doing front-end work your local machine will also need the following dependencies:

[node](https://nodejs.org/en/download/)

[SASS](http://sass-lang.com/)


## Running locally

### Installing
    $ git clone https://github.com/uktrade/directory-sso-profile
    $ cd directory-sso-profile
    $ virtualenv .venv -p python3.6
    $ source .venv/bin/activate
    $ pip install -r requirements_test.txt

### Additional step on OSX

A recent update to OSX removed a particular method from python around SSL. This will cause Captcha to fail in development. This can be re-installed by running the following in terminal: '/Applications/Python\ 3.6/Install\ Certificates.command'. Please read https://stackoverflow.com/questions/27835619/urllib-and-ssl-certificate-verify-failed-error for a more detailed explanation.

### Configuration

Secrets such as API keys and environment specific configurations are placed in `conf/.env` - a file that is not added to version control. You will need to create that file locally in order for the project to run.

Here is an example `conf/.env` with placeholder values to get you going:
```
EXPORTING_OPPORTUNITIES_API_BASE_URL=debug
EXPORTING_OPPORTUNITIES_API_SECRET=debug
EXPORTING_OPPORTUNITIES_SEARCH_URL=debug
GET_ADDRESS_API_KEY=debug
DIRECTORY_FORMS_API_API_KEY=debug
DIRECTORY_FORMS_API_SENDER_ID=debug
```

### Running the webserver
    $ source .venv/bin/activate
    $ make debug_webserver

### Running the tests

    $ make debug_test

## CSS development

If you're doing front-end development work you will need to be able to compile the SASS to CSS. For this you need:

    $ npm install  # to install yarn
    $ yarn install # use yarn for installing all other javascript dependencies

We add compiled CSS files to version control. This will sometimes result in conflicts if multiple developers are working on the same SASS files. However, by adding the compiled CSS to version control we avoid having to install node, npm, node-sass, etc to non-development machines.

You should not edit CSS files directly, instead edit their SCSS counterparts.

### Update CSS under version control

    $ make compile_css

### Rebuild the CSS files when the scss file changes

    $ make watch_css

## Session

Signed cookies are used as the session backend to avoid using a database. We therefore must avoid storing non-trivial data in the session, because the browser will be exposed to the data.


## SSO
To make sso work locally add the following to your machine's `/etc/hosts`:

| IP Adress | URL                  |
| --------  | -------------------- |
| 127.0.0.1 | buyer.trade.great    |
| 127.0.0.1 | supplier.trade.great |
| 127.0.0.1 | sso.trade.great      |
| 127.0.0.1 | api.trade.great      |
| 127.0.0.1 | profile.trade.great  |
| 127.0.0.1 | exred.trade.great    |

Then log into `directory-sso` via `sso.trade.great:8004`, and use `directory-sso-profile` on `profile.trade.great:8006`

Note in production, the `directory-sso` session cookie is shared with all subdomains that are on the same parent domain as `directory-sso`. However in development we cannot share cookies between subdomains using `localhost` - that would be like trying to set a cookie for `.com`, which is not supported by any RFC.

Therefore to make cookie sharing work in development we need the apps to be running on subdomains. Some stipulations:
 - `directory-sso-profile` and `directory-sso` must both be running on sibling subdomains (with same parent domain)
 - `directory-sso` must be told to target cookies at the parent domain.


[code-climate-image]: https://codeclimate.com/github/uktrade/directory-sso-profile/badges/issue_count.svg
[code-climate]: https://codeclimate.com/github/uktrade/directory-sso-profile

[circle-ci-image]: https://circleci.com/gh/uktrade/directory-sso-profile/tree/master.svg?style=svg
[circle-ci]: https://circleci.com/gh/uktrade/directory-sso-profile/tree/master

[codecov-image]: https://codecov.io/gh/uktrade/directory-sso-profile/branch/master/graph/badge.svg
[codecov]: https://codecov.io/gh/uktrade/directory-sso-profile

[gitflow-image]: https://img.shields.io/badge/Branching%20strategy-gitflow-5FBB1C.svg
[gitflow]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow

[calver-image]: https://img.shields.io/badge/Versioning%20strategy-CalVer-5FBB1C.svg
[calver]: https://calver.org
