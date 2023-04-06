from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app import crud, schemas
from app.db.base_class import Base
from app.main import app
from app.api.deps import get_db

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _add_default_values(monitor):
    DEFAULT_MONITOR_PARAMS = {
        "monitor_type": "http",
        "alert_type": "unavailable",
        "auth_pass": None,
        "auth_user": None,
        "keyword": None,
        'periodicity': 120,
        'http_method': 'GET',
        'request_body': None,
        'request_headers': None,
        'request_timeout': 30,
        'follow_redirects': True,
        'keep_cookies_between_redirects': True,
        'verify_ssl': True,
        'ssl_check_expiration': 0,
        'num_pings': 4,
        'port': None,
        'data': None,
        'recovery_period': 0,
        'confirmation_period': 0,
        'send_email': True,
    }
    for key, value in DEFAULT_MONITOR_PARAMS.items():
        if key not in monitor:
            monitor[key] = value
    return monitor


SETUP_USER_EMAIL = 'test@test.com'
SETUP_USER_PASS = 'pass'

@pytest.fixture()
def setup_user(test_db):
    db = next(override_get_db())
    user_in = schemas.UserCreate(password=SETUP_USER_PASS, email=SETUP_USER_EMAIL, full_name='Full Name')
    return crud.user.create(db, obj_in=user_in)

@pytest.fixture()
def setup_active_user(test_db):
    db = next(override_get_db())
    user_in = schemas.UserCreate(password=SETUP_USER_PASS, email=SETUP_USER_EMAIL, full_name='Full Name')
    user_db = crud.user.create(db, obj_in=user_in)
    return crud.user.update(db, db_obj=user_db, obj_in={'is_active': True})

@pytest.fixture()
def setup_access_token(setup_active_user):
    response = client.post(
        "/login/access-token",
        data={
            'username': SETUP_USER_EMAIL,
            'password': SETUP_USER_PASS,
        }
    )

    return response.json()['access_token']


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_monitor_requires_authorization(test_db):
    response = client.post(
        "/monitors",
        json={"endpoint": "https://www.test.com"},
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not authenticated'}


def test_create_monitor_default(setup_access_token):
    response = client.post(
        "/monitors",
        json={"endpoint": "https://www.test.com", "name": "Test"},
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )
    assert response.status_code == 201
    assert response.json() == _add_default_values({
        "id": 1,
        "name": "Test",
        "endpoint": "https://www.test.com",
        "status_since": None,
        "up": None,
    })


def test_create_monitor_unknown_alert_type(setup_access_token):
    response = client.post(
        "/monitors",
        json={"endpoint": "https://www.test.com", "alert_type": "unknown", "name": "Name"},
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [{
                'ctx': {'enum_values': [
                    'unavailable',
                    'contains_keyword',
                    'does_not_contain_keyword'
                ]},
                'loc': ['body', 'alert_type'],
                'msg': "value is not a valid enumeration member; permitted: "
                "'unavailable', 'contains_keyword', 'does_not_contain_keyword'",
                'type': 'type_error.enum',
            }],
    }


def test_create_monitor_fails_if_keyword_not_specified(setup_access_token):
    response = client.post(
        "/monitors",
        json={"endpoint": "https://www.test.com", "alert_type": "contains_keyword", "name": "Name"},
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [{
                'loc': ['body', 'keyword'],
                'msg': "should be defined on alert_type contains_keyword",
                'type': 'value_error.str.condition',
            }],
    }


def test_create_monitor_with_headers(setup_access_token):
    response = client.post(
        "/monitors",
        json={
            "endpoint": "https://www.test.com",
            "name": "Test",
            "request_headers": {
                'Header1 name': 'Header1 value',
            }
        },
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )
    assert response.status_code == 201
    assert response.json() == _add_default_values({
        "id": 1,
        "name": "Test",
        "endpoint": "https://www.test.com",
        "request_headers": {'Header1 name': 'Header1 value'},
        "status_since": None,
        "up": None,
    })


def test_get_empty_monitor_requires_authorization(test_db):
    response = client.get("/monitors")
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not authenticated'}


def test_get_empty_monitor_list(setup_access_token):
    response = client.get(
        "/monitors",
        headers={"Authorization": f"Bearer {setup_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_monitor_list(setup_access_token):
    _ = client.post(
        "/monitors",
        json={
            "name": "Test Monit",
            "endpoint": "https://www.test.com",
            "alert_type": "contains_keyword",
            "keyword": "content",
        },
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )

    response = client.get(
        "/monitors",
        headers={"Authorization": f"Bearer {setup_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == [_add_default_values({
        "id": 1,
        "name": "Test Monit",
        "endpoint": "https://www.test.com",
        "alert_type": "contains_keyword",
        "keyword": "content",
        "status_since": None,
        "up": None,
    })]


# TODO create a monitor of user 1 and another of user 2; request the list of monitors of user 1, and only list its monitor
#def test_get_monitor_list_only_owner_monitors(setup_access_token):
#    pass


def test_get_monitor_requires_authentization(test_db):
    response = client.get("/monitors/1")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_monitor_not_found(setup_access_token):
    response = client.get(
        "/monitors/1",
        headers={"Authorization": f"Bearer {setup_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}


def test_get_monitor(setup_access_token):
    _ = client.post(
        "/monitors",
        json={
            "name": "Test Monit",
            "endpoint": "https://www.test.com",
            "alert_type": "contains_keyword",
            "keyword": "content",
        },
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )

    response = client.get(
        "/monitors/1",
        headers={"Authorization": f"Bearer {setup_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == _add_default_values({
        "id": 1,
        "name": "Test Monit",
        "endpoint": "https://www.test.com",
        "alert_type": "contains_keyword",
        "keyword": "content",
        "status_since": None,
        "up": None,
    })


# TODO test get monitor detail of a monitor not owner by current user


def test_get_monitor_results_filter_bad_format(setup_access_token):
    _ = client.post(
        "/monitors",
        json={
            "name": "Test Monit",
            "endpoint": "https://www.test.com",
        },
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )

    response = client.get(
        "/monitors/1/results",
        params={"since": "bad_datetime"},
        headers={"Authorization": f"Bearer {setup_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [{
            'loc': ['query', 'since'],
            'msg': "invalid datetime format",
            'type': 'value_error.datetime',
        }]
    }


def test_get_monitor_results(setup_access_token):
    response = client.post(
        "/monitors",
        json={
            "name": "Test Monit",
            "endpoint": "https://www.test.com",
        },
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )
    monitor_id = response.json()['id']

    db = next(override_get_db())
    result_obj = schemas.ResultCreate(
        created_at=datetime(2020, 1, 1, 12, 0, 0),
        monitored_at=datetime(2020, 1, 1, 12, 1, 0),
        response_time=0,
        status=False,
        monitor_id=monitor_id,
    )
    db_result = crud.result.create(db, obj_in=result_obj)

    response = client.get(
        f"/monitors/{monitor_id}/results",
        headers={"Authorization": f"Bearer {setup_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == [{
        'id': db_result.id,
        'monitor_id': monitor_id,
        'created_at': datetime(2020, 1, 1, 12, 0, 0).isoformat(),
        'monitored_at':  datetime(2020, 1, 1, 12, 1, 0).isoformat(),
        'response_time': 0,
        'status': False,
    }]


def test_get_monitor_results_since(setup_access_token):
    response = client.post(
        "/monitors",
        json={
            "name": "Name",
            "endpoint": "https://www.test.com",
        },
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )
    monitor_id = response.json()['id']

    db = next(override_get_db())
    result_before = schemas.ResultCreate(
        created_at=datetime(2019, 1, 1, 12, 0, 0),
        monitored_at=datetime(2019, 1, 1, 12, 0, 0),
        response_time=1,
        status=False,
        monitor_id=monitor_id,
    )
    _ = crud.result.create(db, obj_in=result_before)
    result_after = schemas.ResultCreate(
        created_at=datetime(2020, 1, 1, 12, 0, 0),
        monitored_at=datetime(2020, 1, 1, 12, 0, 0),
        response_time=1,
        status=True,
        monitor_id=monitor_id,
    )
    db_result_after = crud.result.create(db, obj_in=result_after)

    response = client.get(
        f"/monitors/{monitor_id}/results",
        params={'since': datetime(2020, 1, 1, 0, 0, 0).isoformat()},
        headers={"Authorization": f"Bearer {setup_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == [{
        'id': db_result_after.id,
        'monitor_id': monitor_id,
        'created_at': datetime(2020, 1, 1, 12, 0, 0).isoformat(),
        'monitored_at': datetime(2020, 1, 1, 12, 0, 0).isoformat(),
        'response_time': 1,
        'status': True,
    }]


@patch('app.tasks.send_user_verification_mail.delay')
def test_create_user(patch_delay, test_db):
    response = client.post(
        "/users",
        json={"email": "test@test.com", "password": "pass", "full_name": 'Name Surname'},
    )

    assert response.status_code == 201
    assert response.json() == {
        'id': 1,
        'email': 'test@test.com',
        'full_name': 'Name Surname',
        'is_active': False,
        'is_superuser': False,
    }


def test_login(setup_active_user):
    response = client.post(
        "/login/access-token",
        data={
            'username': SETUP_USER_EMAIL,
            'password': SETUP_USER_PASS,
        }
    )

    result = response.json()
    assert 'access_token' in result
    assert result['token_type'] == 'bearer'
    assert response.status_code == 200

    response = client.post(
        "/login/test-token",
        headers={
            "Authorization": f"Bearer {result['access_token']}"
        }
    )

    assert response.json()['email'] == SETUP_USER_EMAIL
    assert response.status_code == 200


def test_create_statuspage(setup_access_token):
    db = next(override_get_db())

    monitor = schemas.MonitorCreate(name='test', endpoint='http://google.com')
    db_monitor = crud.monitor.create(db, obj_in=monitor)

    response = client.post(
        "/statuspages",
        json={
            'company_name': 'Your Company',
            'subdomain': 'yourcompany',
            'monitor_ids': [db_monitor.id],
        },
        headers={
            "Authorization": f"Bearer {setup_access_token}"
        }
    )
    assert response.json() == {
        'id': 1,
        'company_name': 'Your Company',
        'company_website': None,
        'subdomain': 'yourcompany',
        'monitor_ids': [db_monitor.id],
    }
    assert response.status_code == 201
