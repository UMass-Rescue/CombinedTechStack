import datetime
import uuid
import os

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from typing import Optional
from jose import JWTError, jwt

from db_connection import get_user_by_name_db, add_user_db, set_user_roles_db, add_api_key_db, get_api_keys_by_user_db, \
    get_api_key_by_key_db, set_api_key_enabled_db

from dependency import pwd_context, logger, oauth2_scheme, TokenData, User, CredentialException, Roles, \
    ExternalServices, APIKeyData
from fastapi import APIRouter, Depends

auth_router = APIRouter()

# to get a string like this run: openssl rand -hex 32
SECRET_KEY = os.getenv('OAUTH2_SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('OAUTH2_TOKEN_EXPIRATION_MINUTES'))


# -------------------------------------------------------------------------------
#
#           OAuth2 Implementation for Server Authentication
#
#           You should not touch this code unless you're sure
#           that you know what you're doing, as changes here can
#           have drastic security consequences server-wide :)
#
# -------------------------------------------------------------------------------


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str):
    user = get_user_by_name_db(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise CredentialException()
        token_data = TokenData(username=username)
    except JWTError:
        raise CredentialException()
    user = get_user_by_name_db(username=token_data.username)
    if user is None or user.disabled:
        raise CredentialException()

    return user


# -------------------------------------------------------------------------------
#
#           User Authentication Helper Methods
#
# -------------------------------------------------------------------------------


def current_user_investigator(token: str = Depends(oauth2_scheme)):
    """
    Permission Checking Function to be used as a Dependency for API endpoints. This is used as a helper.
    This will either return a User object to the calling method if the user meets the authentication requirements,
    or it will raise a CredentialException and prevent the method that depends on this from continuing.

    :param token: User authentication token
    :return: User object if user has correct role, else raise dependency.CredentialException
    """
    user = get_current_user(token)
    if not any(role in [Roles.admin.name, Roles.investigator.name] for role in user.roles):
        raise CredentialException()

    return user


def current_user_researcher(token: str = Depends(oauth2_scheme)):
    """
    Permission Checking Function to be used as a Dependency for API endpoints. This is used as a helper.
    This will either return a User object to the calling method if the user meets the authentication requirements,
    or it will raise a CredentialException and prevent the method that depends on this from continuing.

    :param token: User authentication token
    :return: User object if user has correct role, else raise dependency.CredentialException
    """
    user = get_current_user(token)
    if not any(role in [Roles.admin.name, Roles.researcher.name] for role in user.roles):
        raise CredentialException()

    return user


def current_user_admin(token: str = Depends(oauth2_scheme)):
    """
    Permission Checking Function to be used as a Dependency for API endpoints. This is used as a helper.
    This will either return a User object to the calling method if the user meets the authentication requirements,
    or it will raise a CredentialException and prevent the method that depends on this from continuing.

    :param token: User authentication token
    :return: User object if user has correct role, else raise dependency.CredentialException
    """
    user = get_current_user(token)
    if Roles.admin.name not in user.roles:
        raise CredentialException()

    return user


# -------------------------------------------------------------------------------
#
#           User Authentication Endpoints
#
# -------------------------------------------------------------------------------

@auth_router.post('/add_role', dependencies=[Depends(current_user_admin)])
def add_permission_to_user(username, role):
    """
    Allows administrators to add permissions to a user account. Permissions allow for a user to access certain
    endpoints and features that are not available to the general user base.

    :param username: Username of account to modify
    :param role: dependency.Roles to add to account, as a string
    :return: {'status': 'success'} if role modification successful, else {'status': 'failure'}
    """

    user = get_user_by_name_db(username)
    if not user:
        return JSONResponse(
            status_code=404,
            content={
                'detail': 'Unable to find user with given username.',
                'username': username
            }
        )

    # Ensure that the role name is valid
    if role not in list(Roles.__members__):
        return JSONResponse(
            status_code=404,
            content={
                'detail': 'Unable to find role with given name.',
                'valid_roles': list(Roles.__members__),
                'invalid_role_provided': role
            }
        )

    if role in user.roles:
        return {
            'detail': 'User already has role. No changes made.',
            'username': str(username),
            'user_roles': user.roles
        }

    user_new_role_list = user.roles.copy()
    user_new_role_list.append(role)
    set_user_roles_db(username, user_new_role_list)

    return {
        'detail': 'User successfully added to role.',
        'username': str(username),
        'user_roles': user.roles
    }


@auth_router.post('/remove_role', dependencies=[Depends(current_user_admin)])
def remove_permission_from_user(username: str, role: str):
    """
    Allows administrators to remove permissions from a user account. Permissions allow for a user to access certain
    endpoints and features that are not available to the general user base.

    :param username: Username of account to modify
    :param role: dependency.Roles to remove from account, as a string
    :return: {'status': 'success'} if role modification successful, else {'status': 'failure'}
    """

    user = get_user_by_name_db(username)

    if not user:
        return JSONResponse(
            status_code=404,
            content={
                'detail': 'Unable to find user with given username.',
                'username': username
            }
        )

    # Ensure that the role name is valid
    if role not in list(Roles.__members__):
        return JSONResponse(
            status_code=404,
            content={
                'detail': 'Unable to find role with given name.',
                'valid_roles': list(Roles.__members__),
                'invalid_role_provided': role
            }
        )

    if role not in user.roles:
        return {
            'detail': 'User does not have role. No changes made.',
            'username': str(username),
            'user_roles': user.roles
        }

    user_new_role_list = user.roles.copy()
    user_new_role_list.remove(role)
    set_user_roles_db(username, user_new_role_list)
    return {
        'detail': 'Successfully removed role from user.',
        'username': str(username),
        'user_roles': user.roles
    }


@auth_router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Logs current user in by validating their credentials and then issuing a new OAuth2 bearer token. This token
    is only valid for a fixed amount of time (ACCESS_TOKEN_EXPIRE_MINUTES) and after this has passed the user
    must log back in again.

    :param form_data: HTTP FormData containing login credentials
    :return: OAuth2 bearer token if login successful, else 401 unauthorized response
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        return JSONResponse(
            status_code=401,
            content={
                'detail': 'Unable to authenticate. Please ensure that username and password are correct.'
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {
        'detail': 'Login successful.',
        "access_token": access_token,
        "token_type": "bearer"
    }


@auth_router.post('/new')
def create_account(username: str, password: str, email: str = None, full_name: str = None, agency: str = None):
    """
    Creates a new user account with specified information. No permissions are granted upon account creation
    and an administrator must manually add permissions to an account before it is able to access most endpoints.

    :param username: Username of new account. Must be unique
    :param password: Password of new account. This is immediately hashed and never stored in plaintext
    :param email: (optional) Email address associated with new account.
    :param full_name:(optional) User's full name (First + Last) as a single string
    :param agency: (optional) Agency/Organization associated with the new user as a string
    :return: {'status': 'success'} if account creation successful, else {'status': 'failure'}
    """
    u = User(
        username=username,
        password=get_password_hash(password),
        email=email,
        full_name=full_name,
        roles=[],
        agency=agency
    )

    result = add_user_db(u)

    if not result:
        return JSONResponse(
            status_code=409,
            content={
                'detail': 'Account with given username already exists. Please select a name that is not in use.',
                'username': username
            },
        )

    return {
        'detail': 'Account created successfully.',
        'username': username
    }


@auth_router.get("/status")
def get_login_status(current_user: User = Depends(get_current_user)):
    """
    Check if the current user is authenticated.

    :return: Current username if logged in, else dependency.CredentialException
    """

    return {
        'detail': 'Authentication successful.',
        'username': current_user.username
    }


@auth_router.get("/profile")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Export the data of the current user to the client.

    :param current_user: Currently logged in user to have data exported. This field is auto filled by the HTTP request
    :return: User profile details, excluding hashed password.
    """
    user_export_data = current_user.dict(exclude={'password', 'id'})
    return user_export_data


# -------------------------------------------------------------------------------
#
#           API Key Endpoints
#
# -------------------------------------------------------------------------------

@auth_router.post('/key', dependencies=[Depends(current_user_researcher)])
def add_api_key(key_owner_username: str, service: str, detail: str = ""):
    """
    Creates a new API key belonging to a user and associated with a service. This key is only able to be
    used on this specific service, and will be immediately enabled upon creation. The unique API Key string
    that is returned is used for all authentication between external services and the server.

    :param key_owner_username: Username of user who 'owns' this API Key
    :param service: dependency.ExternalService object name of microservice this key is associated with
    :param detail: (optional) A brief description of what the key is used for
    :return: Key data if successful. Else, HTTP exception
    """

    user = get_user_by_name_db(key_owner_username)

    if not user:
        return JSONResponse(
            status_code=404,
            content={
                'detail': 'Desired Key owner username does not exist. Unable to create API key.',
                'username': key_owner_username
            }
        )

    # Ensure that the service name for the key is valid
    if service not in list(ExternalServices.__members__):
        return JSONResponse(
            status_code=404,
            content={
                'detail': 'Service specified does not exist. Unable to create API key.',
                'valid_services': list(ExternalServices.__members__),
                'invalid_service_in_request': service
            }
        )

    api_key_string = str(uuid.uuid4())

    api_key_object = APIKeyData(**{
        'key': api_key_string,
        'type': service,
        'user': key_owner_username,
        'detail': detail,
        'enabled': True
    })

    result = add_api_key_db(api_key_object)

    # If successful, return success message and the API key object
    if result['status'] == 'success':
        return {
            **api_key_object.dict()
        }
    else:
        return JSONResponse(
            status_code=500,
            content={
                'detail': 'Unable to add API key.',
            }
        )


@auth_router.get('/key')
def get_api_key(current_user: User = Depends(get_current_user)):
    """
    Gets all API keys associated with the user making the request. This method will only return keys
    that are in good standing and that are enabled.

    :param current_user: Currently logged in user. This is automatically parsed from the request.
    :return: List of all API keys for the user. If none exist, then 'keys' field is empty.
    """
    all_user_keys = get_api_keys_by_user_db(current_user)

    return {
        'keys': all_user_keys
    }


@auth_router.delete('/key')
def disable_api_key(key: str, current_user: User = Depends(get_current_user)):
    """
    Disables an existing API Key. This requires that either the user making the request is the API Key owner or
    that the user making the request is an administrator. This does not delete the key from the database, but leaves
    it in a disabled state for future reference.

    :param key: API Key string to disable
    :param current_user: Currently logged in user. This is automatically parsed from the request.
    :return: success response if disabled successfully, else HTTP Exception
    """
    key = get_api_key_by_key_db(key)

    if not key:
        return JSONResponse(
            status_code=404,
            content={
                'detail': 'Invalid API key provided. Unable to delete',
                'key': key
            }
        )

    # If it is not the user's key and they are not an admin, then don't allow key to be disabled.
    if key.user != current_user.username and Roles.admin.name not in current_user.roles:
        raise CredentialException

    set_api_key_enabled_db(key, False)
    return {
        'detail': 'API key has been removed.',
        'key': key,
    }


# -------------------------------------------------------------------------------
#
#           Administration and Testing Endpoints
#
# -------------------------------------------------------------------------------


@auth_router.post('/create_admin_account')
def create_admin_account_testing():

    if get_user_by_name_db('admin'):
        return JSONResponse(
            status_code=409,
            content={
                'detail': 'Admin account already exists.',
                'username': 'admin',
                'password': 'password'
            }
        )

    u = User(
        username='admin',
        password=get_password_hash('password'),
        email='admin@email.com',
        roles=['admin']
    )

    add_user_db(u)

    return {
        'detail': 'Admin account has been created.',
        'username': 'admin',
        'password': 'password'
    }


def create_testing_account():
    """
    Creates an account for usage in tests. This account should never be logged into, and is only accessed by
    username in test cases
    """

    # Only create a testing account if it doesn't exist already
    if not get_user_by_name_db('testing'):
        password = str(uuid.uuid4())
        u = User(
            username='testing',
            password=get_password_hash(password),  # Random unguessable password
            email='testing@test.com',
            roles=['admin'],
            agency=password
        )

        add_user_db(u)


def create_testing_keys():
    """
    Creates API keys for usage in test cases. These keys should NEVER be used for actual microservices.
    """

    # Only create an API key testing account if it doesn't exist already
    if not get_user_by_name_db('api_key_testing'):
        password = str(uuid.uuid4())
        u = User(
            username='api_key_testing',
            password=get_password_hash(password),  # Random unguessable password
            email='api_key_testing@test.com',
            roles=['admin'],
        )
        add_user_db(u)
    else:
        u = get_user_by_name_db('api_key_testing')

    # If keys do not already exist, create them
    if not get_api_keys_by_user_db(u):

        prediction_key_value = str(uuid.uuid4())
        training_key_value = str(uuid.uuid4())

        prediction_key = APIKeyData(**{
            'key': prediction_key_value,
            'type': ExternalServices.predict_microservice.name,
            'user': 'api_key_testing',
            'detail': 'Key For Testing ONLY',
            'enabled': True
        })

        training_key = APIKeyData(**{
            'key': training_key_value,
            'type': ExternalServices.train_microservice.name,
            'user': 'api_key_testing',
            'detail': 'Key For Testing ONLY',
            'enabled': True
        })

        add_api_key_db(prediction_key)
        add_api_key_db(training_key)


