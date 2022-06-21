
tokenstore
==========

TODO: update this !!!!!

Quick intro of project goes here.

Installation
============

.. code:: bash

    pip install tokenstore


Configuration
=============

The application can configured like any other Flask application.

First it will load the bundled `settings.py` file to configure sensible defaults.
Please see `settings.py` and https://terndatateam.bitbucket.io/flask_tern/ for details.

Next it will look for an environment variable `TOKENSTORE_SETTINGS`. This environment variable
should point to a python file which will be loaded as well. The format is exactly the same as in `settings.py` .

This project uses ``flask_tern``. Be sure to check documentation and code https://bitbucket.org/terndatateam/flask_tern .

Flask-Cors: https://flask-cors.readthedocs.io/en/latest/


Development
===========

Clone the source code and cd into the directory of your local copy.
You may want to adapt settings in .flaskenv

.. code:: bash

    # install project in editable mode
    pip install -e '.[testing,docs]'
    # to run tests use
    pytest
    # coverage report
    pytest --cov --cov-report=html


The same can be done within a docker environment. The following is a simple example using alpine.

.. code:: bash

    docker run --rm -it -p 5000:5000 -v "$(pwd)":/tokenstore -w /tokenstore alpine:3.10 sh
    # install python in binary libs in container
    apk add python3 py3-cryptography
    # install pkg in container
    pip3 install -e '.[testing]'
    # run tests inside container
    pytest
    pytest --cov --cov-report=html


Run flask development server.

.. code:: bash

    # locally
    flask run
    # within container
    flask run -h 0.0.0.0

The app can then be accessed at http://localhost:5000


Database management
===================

The project uses Flask-Migrate to manage databes schemas.
Flask-Migrate uses Alembic to manage database migrations.
Whenever there are changes to the database models, it is necessary to create a new migration step and apply this migration to the database.
Per default the development environment uses sqlite as database backend, but this can easily be change by reconfiguring Flask-SQLAlchemy.

.. code:: bash

    # the following two steps are necessary when changing database models
    # create new mgration / revision
    flask db migrate

    # update / create db. this step also initialises an empty database with the latest db schema.
    flask db upgrade

Configuration
=============

Configuration can be done via environment variables or a settings file. A settings file is interpreted as Python file (it does not need to end in ```.py``)
and should defines all configuration options as module global variables (all capitals). The same config options can be set as environment variables. Each
environment variable needs to be prefixed with ``TOKENSTORE_``.

To set the location of a configuration file it is necessare to set the env var ``TOKENSTORE_SETTINGS`` to point to a file (full path to config file).

The examples below show the config options as they would be used in a config file. The same settings can be achieved via env vars prefixed by ``TOKENSTORE_``

.. code:: bash

    # example to configure database connection via env ars
    export TOKENSTORE_SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@postgres:5432/tokenstore


Session handling
----------------

Use this to configure session handling via https://flask-session.readthedocs.io/en/latest/

    .. code:: python

        SESSION_TYPE = "filesystem"
        SESSION_FILE_DIR = "/tmp/sessions"


Database connection
-------------------

    Configure sql alchemy databes uri

    .. code:: python

        SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@postgres:5432/tokenstore"


Authentication
--------------

Use OpenID Connect to authenticate users

    .. code:: python

        OIDC_DISCOVERY_URL = "https://auth.example.com/auth/realms/example/.well-known/openid-configuration"
        OIDC_CLIENT_ID = "tokenstore"
        OIDC_CLIENT_SECRET = "tokenstore_client_secret"


Token providers
---------------

Configure one or more external OIDC / OAuth2 clients for which this service can manage tokens.

    .. code::

        # comma separated list of OIDC clients  (these are the id's used in the api)
        TOKEN_PROVIDERS = "idp1, idp2"

        # configure each token provider (id is capitalized for config option)
        IDP1_DISCOVERY_URL = "https://auth-idp1.example.com/auth/realms/example/.well-known/openid-configuration"
        IDP1_CLIENT_ID = "idp1"
        IDP1_CLIENT_SECRET = "idp1_client_secret"
        # optional metadata ... this data is returned via the API, and can be used by a UI
        IDP1_MD_NAME = "IDP1 Display Name"
        IDP1_MD_DESCRIPTION = "IDP1 description text"
        IDP1_MD_URL = "IDP1 Home page"
        IDP1_MD_ICON = "IDP1 Icon url"
        IDP1_MD_LOGO = "IDP1 Logo url"

        # do the same for IDP2 as above
        IDP2_DISCOVERY_URL = "https://auth-idp2.example.com/auth/realms/example/.well-known/openid-configuration"
        IDP2_CLIENT_ID = "idp2"
        IDP2_CLIENT_SECRET = "idp2_client_secret"
        # optional metadata can be set the same way
        IDP2_MD_NAME = "IDP2 Display Name"
        IDP2_MD_DESCRIPTION = "IDP2 description text"
        IDP2_MD_URL = "IDP2 Home page"
        IDP2_MD_ICON = "IDP2 Icon url"
        IDP2_MD_LOGO = "IDP2 Logo url"
