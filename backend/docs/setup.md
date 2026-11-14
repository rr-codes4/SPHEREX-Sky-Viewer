# Development setup

## Create the environment

From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pip install --no-deps -e backend
```

The package requires Python 3.11 or later. All backend-specific files remain
inside `backend/`; do not modify root dependency or configuration files.

## Run tests

```bash
PYTHONPATH=backend/src backend/.venv/bin/python -m pytest backend/tests
```

The standard suite uses mocks and local temporary files. It does not require
IRSA availability.

To run the live integration test explicitly:

```bash
RUN_IRSA_INTEGRATION=1 PYTHONPATH=backend/src \
  backend/.venv/bin/python -m pytest backend/tests/integration -m integration
```

## Development workflow

1. Keep source under `backend/src/astronomy_backend/`.
2. Add focused tests under `backend/tests/`.
3. Use `astropy.units` for angular values.
4. Preserve source metadata when normalizing records.
5. Run the standard suite and `git diff --check`.
6. Stage only backend-specific files.
