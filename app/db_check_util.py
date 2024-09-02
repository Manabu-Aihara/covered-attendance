from app import db
from app.models import User, D_JOB_HISTORY


def check_different_value(target_id: int):
    target_staff_info = (
        db.session.query(User.CONTRACT_CODE, User.JOBTYPE_CODE)
        .filter(User.STAFFID == target_id)
        .first()
    )
    target_contract_info = (
        db.session.query(D_JOB_HISTORY.CONTRACT_CODE, D_JOB_HISTORY.JOBTYPE_CODE)
        .filter(D_JOB_HISTORY.STAFFID == target_id)
        .first()
    )
    if target_contract_info is None:
        raise TypeError("スルーします")
    else:
        if (
            target_staff_info.CONTRACT_CODE != target_contract_info.CONTRACT_CODE
            or target_staff_info.JOBTYPE_CODE != target_contract_info.JOBTYPE_CODE
        ):
            # raise ValueError("テーブル間で、雇用形態及び勤務形態が合致していません")
            return target_id
        else:
            return None


def _check_error_handler(func):
    def wrapper(staff_id: int, *args, **kwargs):
        try:
            print(args)
            value = check_different_value(staff_id)
        except TypeError as e:
            print(e)
        # except ValueError as e:
        #     print(f"{staff_id}: {e}")
        else:
            return func(value, *args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def check_error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(args, kwargs)
        except TypeError as e:
            print(e)
        except ValueError as e:
            print(e)

    wrapper.__name__ = func.__name__
    return wrapper


def compare_db_item(staff_id: int):
    try:
        caution_id = check_different_value(staff_id)
    except TypeError as e:
        print(e)
    else:
        return caution_id
