# directory-sso-profile

This is the repository for EIG Single User Dashboard (SUD) - the Department for International Trade (DIT) service for managing EIG profiles.

## Build status

[![CircleCI](https://circleci.com/gh/uktrade/directory-sso-profile/tree/master.svg?style=svg)](https://circleci.com/gh/uktrade/directory-sso-profile/tree/master)

## Development 

The back-end framework is Django 1.9. The front-end uses minimal Javascript. The motivation for this is for accessibility reasons, to reduce technical complexity, and reduce cross-browser compatibility issues. Therefore most front-end work will be HTML and SASS/CSS development.

We aim to follow [GDS service standards](https://www.gov.uk/service-manual/service-standard) and [GDS design principles](https://www.gov.uk/design-principles).

## Requirements
[Python 3.5](https://www.python.org/downloads/release/python-352/)

### Docker

[Docker >= 1.10](https://docs.docker.com/engine/installation/)

[Docker Compose >= 1.8](https://docs.docker.com/compose/install/)

### SASS
We use SASS CSS pre-compiler. If you're doing front-end work your local machine will also need the following dependencies:

[node](https://nodejs.org/en/download/)

[SASS](http://sass-lang.com/)

## Running locally with Docker
This requires all host environment variables to be set.

    $ make docker_run

### Run debug webserver in Docker

    $ make docker_debug

### Run tests in Docker

    $ make docker_test

### Host environment variables for docker-compose
``.env`` files will be automatically created (with ``env_writer.py`` based on ``env.json``) by ``make docker_test``, based on host environment variables with ``DIRECTORY_UI_BUYER_`` prefix.


## Running locally without Docker

### Installing
    $ git clone https://github.com/uktrade/directory-sso-profile
    $ cd directory-sso-profile
    $ virtualenv .venv -p python3.5
    $ source .venv/bin/activate
    $ pip install -r requirements_test.txt

### Running the webserver
    $ source .venv/bin/activate
    $ make debug_webserver

### Running the tests

    $ make debug_test

### CSS development

If you're doing front-end development work you will need to be able to compile the SASS to CSS. For this you need:

```bash
npm install
npm run sass-prod
```

We add compiled CSS files to version control. This will sometimes result in conflicts if multiple developers are working on the same SASS files. However, by adding the compiled CSS to version control we avoid having to install node, npm, node-sass, etc to non-development machines.

You should not edit CSS files directly, instead edit their SCSS counterparts.

# Session

Signed cookies are used as the session backend to avoid using a database. We therefore must avoid storing non-trivial data in the session, because the browser will be exposed to the data.


# SSO
To make sso work locally add the following to your `/etc/hosts`:
127.0.0.1 ui.trade.great.dev
127.0.0.1 sso.trade.great.
127.0.0.1 api.trade.great.dev

Then log into `directory-sso` via `sso.trade.great.dev:8001`, and use `directory-sso-profile` on `ui.trade.great.dev:8001`

Note in production, the `directory-sso` session cookie is shared with all subdomains that are on the same parent domain as `directory-sso`. However in development we cannot share cookies between subdomains using `localhost` - that would be like trying to set a cookie for `.com`, which is not supported any any RFC.

Therefore to make cookie sharing work in development we need the apps to ne running on subdomains. Some stipulations:
 - `directory-sso-profile` and `directory-sso` must both be running on sibling subdomains (with same parent domain)
 - `directory-sso` must be told to target cookies at the parent domain.
