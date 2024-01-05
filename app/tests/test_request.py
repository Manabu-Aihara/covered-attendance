from app import app

def test_get_request_in_confirm():
    response = app.test_client().get('/confirm')
    print(response.data)
    assert response is not None