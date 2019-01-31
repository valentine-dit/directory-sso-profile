from enrolment import forms


def test_password_verify_password_not_matching():
    form = forms.UserAccount(
        data={'password': 'password', 'password_confirmed': 'drowssap'}
    )

    assert form.is_valid() is False
    assert "Passwords don't match" in form.errors['password_confirmed']
