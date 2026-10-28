from app.auth.tokens import create_access_token, create_admin_access_token


def make_customer_headers(user_id: str = "test-user", customer_id: str = "test-customer") -> dict:
    token = create_access_token(user_id, customer_id)
    return {"Authorization": f"Bearer {token}"}


def make_admin_headers(user_id: str = "admin") -> dict:
    token = create_admin_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}
