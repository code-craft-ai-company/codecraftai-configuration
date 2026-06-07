==============================
Code Craft AI Configuration
==============================

The ``codecraftai-configuration`` package is the configuration-loading and synchronisation layer for the ccai suite. It lets applications and tests pull configuration from a mix of local and remote sources, merge it through well-defined overrides, and (optionally) keep local copies in sync with a remote authority. It depends on ``codecraftai-errors`` and ``codecraftai-credentials``, and is consumed widely across the suite.

Highlights
==========

- ``ConfigurationLoader`` top-level entry point that reads from a list of source URIs and produces a merged, normalised configuration.
- Pluggable ``ConfigurationSourceBase`` with concrete sources: ``DirectorySource``, ``HttpSource``, ``CouchDBSource``, and ``MongoDBSource``.
- ``ConfigSynchronizerBase`` family with ``DirectoryConfigSynchronizer``, ``CouchDBConfigSynchronizer``, ``MongoDBConfigSynchronizer``, and ``GithubConfigSynchronizer``.
- Supporting modules for formats, Fernet-based cryptography, option overrides, default values, and normalisation.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/`` - Package source code.
- ``source/tests/`` - ``unittest``-based tests.
- ``specs/`` - Requirements, design, and task documentation.
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container:

.. code-block:: bash

   ./development/setup-agent-container

For local development:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-envrionment

Running Tests
=============

Activate the virtual environment:

.. code-block:: bash

   source .venv/bin/activate

Run ``unittest`` tests:

.. code-block:: bash

   python -m unittest discover -s source/tests -p "test_*.py"

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Design documentation: ``specs/design.md``
- Requirements: ``specs/requirements.md``
