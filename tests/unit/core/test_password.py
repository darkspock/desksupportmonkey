from core.password import PasswordService


class TestPasswordService:
    def test_hash_and_verify_roundtrip(self):
        svc = PasswordService()
        hashed = svc.hash_password("mysecretpass")
        assert svc.verify_password("mysecretpass", hashed) is True

    def test_wrong_password_fails(self):
        svc = PasswordService()
        hashed = svc.hash_password("correctpassword")
        assert svc.verify_password("wrongpassword", hashed) is False

    def test_hash_is_not_plaintext(self):
        svc = PasswordService()
        hashed = svc.hash_password("test1234")
        assert hashed != "test1234"
        assert hashed.startswith("$2")
