foris-controller-matter-module
==============================

Matter network manager module for foris-controller. It exposes the ``matter``
ubus object published by the Matter Network Infrastructure Manager app, so a
web frontend such as reForis can show the router's onboarding information and
control its commissioning window without ubus access of its own.

The module is the Matter half of the reForis Thread/Matter plugin's backend;
the Thread side lives in ``foris-controller-thread-module``.

Requirements
------------

* python3
* foris-controller
* matter-netman (providing the ``matter`` ubus object)
* qrencode, optionally, for server-side QR rendering

Installation
------------

::

    pip install .

Actions
-------

``get_onboarding``
    Onboarding status. ``present`` false means no Matter manager is installed
    here; ``present`` with ``live`` false means one is installed but its daemon
    is not answering, which is read from the factory configuration on disk. The
    pairing code and the QR payload are included only while a commissioning
    window is open, because that is the only time they authenticate -- a page
    that always showed the code would suggest pairing is always possible.

``open_window`` / ``close_window``
    Local control of the commissioning window.

``remove_fabric``
    Unpair a controller. The daemon validates the index.

Testing
-------

::

    pip install -e .[tests]
    pytest -vv tests
