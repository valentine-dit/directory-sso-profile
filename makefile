build: docker_test

clean:
	-find . -type f -name "*.pyc" -delete
	-find . -type d -name "__pycache__" -delete

test_requirements:
	pip install -r requirements_test.txt

FLAKE8 := flake8 . --exclude=.venv
PYTEST := pytest . --cov=. --cov-config=.coveragerc --cov-report=html --cov-report=term --capture=no $(pytest_args)
COLLECT_STATIC := python manage.py collectstatic --noinput

test:
	$(COLLECT_STATIC) && $(FLAKE8) && $(PYTEST)

DJANGO_WEBSERVER := \
	python manage.py collectstatic --noinput && \
	python manage.py runserver 0.0.0.0:$$PORT

django_webserver:
	$(DJANGO_WEBSERVER)

DOCKER_COMPOSE_REMOVE_AND_PULL := docker-compose -f docker-compose.yml -f docker-compose-test.yml rm -f && docker-compose -f docker-compose.yml -f docker-compose-test.yml pull
DOCKER_COMPOSE_CREATE_ENVS := python ./docker/env_writer.py ./docker/env.json ./docker/env.test.json

docker_run:
	$(DOCKER_COMPOSE_CREATE_ENVS) && \
	$(DOCKER_COMPOSE_REMOVE_AND_PULL) && \
	docker-compose up --build

DOCKER_SET_DEBUG_ENV_VARS := \
	export SSO_PROFILE_SECRET_KEY=debug; \
	export SSO_PROFILE_DEBUG=true ;\
	export SSO_PROFILE_SSO_API_CLIENT_KEY=api_signature_debug; \
	export SSO_PROFILE_SSO_API_CLIENT_BASE_URL=http://sso.trade.great.dev:8004/api/v1/; \
	export SSO_PROFILE_SSO_LOGIN_URL=http://sso.trade.great.dev:8004/accounts/login/?next=http://profile.trade.great.dev:8006; \
	export SSO_PROFILE_SSO_LOGOUT_URL=http://sso.trade.great.dev:8004/accounts/logout/?next=http://profile.trade.great.dev:8006; \
	export SSO_PROFILE_SSO_PASSWORD_RESET_URL=http://sso.trade.great.dev:8004/accounts/password/reset/; \
	export SSO_PROFILE_SSO_SIGNUP_URL=http://sso.trade.great.dev:8004/accounts/signup/?next=http://profile.trade.great.dev:8006; \
	export SSO_PROFILE_SSO_PROFILE_URL=http://profile.trade.great.dev:8006; \
	export SSO_PROFILE_SSO_REDIRECT_FIELD_NAME=next; \
	export SSO_PROFILE_SSO_SESSION_COOKIE=debug_sso_session_cookie; \
	export SSO_PROFILE_SESSION_COOKIE_SECURE=false; \
	export SSO_PROFILE_UTM_COOKIE_DOMAIN=.great.dev; \
	export SSO_PROFILE_GOOGLE_TAG_MANAGER_ID=GTM-TC46J8K; \
	export SSO_PROFILE_GOOGLE_TAG_MANAGER_ENV=&gtm_auth=kH9XolShYWhOJg8TA9bW_A&gtm_preview=env-32&gtm_cookies_win=x; \
	export SSO_PROFILE_DIRECTORY_API_EXTERNAL_CLIENT_BASE_URL=http://buyer.trade.great.dev:8001/api/external/; \
	export SSO_PROFILE_DIRECTORY_API_EXTERNAL_CLIENT_KEY=debug; \
	export SSO_PROFILE_DIRECTORY_API_EXTERNAL_CLIENT_CLASS_NAME='unit-test'; \
	export SSO_PROFILE_EXPORTING_OPPORTUNITIES_API_BASIC_AUTH_USERNAME=debug; \
	export SSO_PROFILE_EXPORTING_OPPORTUNITIES_API_BASIC_AUTH_PASSWORD=debug; \
	export SSO_PROFILE_EXPORTING_OPPORTUNITIES_API_BASE_URL=https://staging-new-design-eig.herokuapp.com/; \
	export SSO_PROFILE_EXPORTING_OPPORTUNITIES_API_SECRET=debug; \
	export SSO_PROFILE_EXPORTING_OPPORTUNITIES_SEARCH_URL=https://opportunities.export.great.gov.uk/opportunities; \
	export SSO_PROFILE_FAB_EDIT_COMPANY_LOGO_URL=http://buyer.trade.great.dev:8001/company-profile/edit/logo; \
	export SSO_PROFILE_FAB_EDIT_PROFILE_URL=http://buyer.trade.great.dev:8001/company-profile; \
	export SSO_PROFILE_FAB_ADD_CASE_STUDY_URL=http://buyer.trade.great.dev:8001/company/case-study/edit/

DOCKER_REMOVE_ALL := \
	docker ps -a | \
	grep profile | \
	awk '{print $$1 }' | \
	xargs -I {} docker rm -f {}

docker_remove_all:
	$(DOCKER_REMOVE_ALL)

docker_debug: docker_remove_all
	$(DOCKER_SET_DEBUG_ENV_VARS) && \
	$(DOCKER_COMPOSE_CREATE_ENVS) && \
	docker-compose pull && \
	docker-compose build && \
	docker-compose run --service-ports webserver make django_webserver

docker_webserver_bash:
	docker exec -it directoryui_webserver_1 sh

docker_test: docker_remove_all
	$(DOCKER_SET_DEBUG_ENV_VARS) && \
	$(DOCKER_COMPOSE_CREATE_ENVS) && \
	$(DOCKER_COMPOSE_REMOVE_AND_PULL) && \
	docker-compose -f docker-compose-test.yml build && \
	docker-compose -f docker-compose-test.yml run sut

docker_build:
	docker build -t ukti/directory-sso-profile:latest .

DEBUG_TEST_SET_ENV_VARS := \
	export DIRECTORY_API_EXTERNAL_CLIENT_CLASS_NAME='unit-test'

DEBUG_SET_ENV_VARS := \
	export PORT=8006; \
	export SECRET_KEY=debug; \
	export DEBUG=true ;\
	export SSO_API_CLIENT_KEY=api_signature_debug; \
	export SSO_API_CLIENT_BASE_URL=http://sso.trade.great.dev:8004/api/v1/; \
	export SSO_LOGIN_URL=http://sso.trade.great.dev:8004/accounts/login/?next=http://profile.trade.great.dev:8006; \
	export SSO_LOGOUT_URL=http://sso.trade.great.dev:8004/accounts/logout/?next=http://profile.trade.great.dev:8006; \
	export SSO_PASSWORD_RESET_URL=http://sso.trade.great.dev:8004/accounts/password/reset/; \
	export SSO_SIGNUP_URL=http://sso.trade.great.dev:8004/accounts/signup/?next=http://profile.trade.great.dev:8006; \
	export SSO_REDIRECT_FIELD_NAME=next; \
	export SSO_SESSION_COOKIE=debug_sso_session_cookie; \
	export SSO_PROFILE_URL=http://profile.trade.great.dev:8006; \
	export SESSION_COOKIE_SECURE=false; \
	export UTM_COOKIE_DOMAIN=.great.dev; \
	export GOOGLE_TAG_MANAGER_ID=GTM-TC46J8K; \
	export GOOGLE_TAG_MANAGER_ENV=&gtm_auth=kH9XolShYWhOJg8TA9bW_A&gtm_preview=env-32&gtm_cookies_win=x; \
	export DIRECTORY_API_EXTERNAL_CLIENT_BASE_URL=http://buyer.trade.great.dev:8001/api/external/; \
	export DIRECTORY_API_EXTERNAL_CLIENT_KEY=debug; \
	export EXPORTING_OPPORTUNITIES_API_BASIC_AUTH_USERNAME=debug; \
	export EXPORTING_OPPORTUNITIES_API_BASIC_AUTH_PASSWORD=debug; \
	export EXPORTING_OPPORTUNITIES_API_BASE_URL=https://staging-new-design-eig.herokuapp.com/; \
	export EXPORTING_OPPORTUNITIES_API_SECRET=debug; \
	export EXPORTING_OPPORTUNITIES_SEARCH_URL=https://opportunities.export.great.gov.uk/opportunities; \
	export FAB_EDIT_COMPANY_LOGO_URL=http://buyer.trade.great.dev:8001/company-profile/edit/logo; \
	export FAB_EDIT_PROFILE_URL=http://buyer.trade.great.dev:8001/company-profile; \
	export FAB_ADD_CASE_STUDY_URL=http://buyer.trade.great.dev:8001/company/case-study/edit/

debug_webserver:
	$(DEBUG_SET_ENV_VARS) && $(DJANGO_WEBSERVER)

debug_pytest:
	$(DEBUG_SET_ENV_VARS) && \
	$(DEBUG_TEST_SET_ENV_VARS) && \
	$(COLLECT_STATIC) && \
	$(PYTEST)

debug_test:
	$(DEBUG_SET_ENV_VARS) && \
	$(DEBUG_TEST_SET_ENV_VARS) && \
	$(COLLECT_STATIC) && \
	$(FLAKE8) && \
	$(PYTEST)

debug_manage:
	$(DEBUG_SET_ENV_VARS) && ./manage.py $(cmd)

debug_shell:
	$(DEBUG_SET_ENV_VARS) && ./manage.py shell

debug: test_requirements debug_test

heroku_deploy_dev:
	docker build -t registry.heroku.com/directory-sso-profile-dev/web .
	docker push registry.heroku.com/directory-sso-profile-dev/web

smoke_tests:
	cd $(mktemp -d) && \
	git clone https://github.com/uktrade/directory-tests && \
	cd directory-tests && \
	make docker_smoke_test

.PHONY: build clean test_requirements docker_run docker_debug docker_webserver_bash docker_test debug_webserver debug_test debug heroku_deploy_dev heroku_deploy_demo
