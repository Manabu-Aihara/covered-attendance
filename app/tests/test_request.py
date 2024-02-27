from app import db

from app.dummy_model_todo import TodoOrm

# def test_get_request_in_confirm():
#     response = app.test_client().get('/confirm')
#     print(response.data)
#     assert response is not None


def test_get_todo_list(app_context):
    td_dict_list = []
    todo_list: list = db.session.query(TodoOrm).all()
    for todo in todo_list:
        td_dict_list.append(todo.to_dict())

    print(td_dict_list)
