# xlsx2md

The repository root is the `xlsx2md` Python package. After cloning and installing requirements, run the package **from the parent directory of the clone**:

```bash
git clone https://github.com/rarnhe/xlsx2md.git
python -m pip install -r xlsx2md/requirements.txt
python -m xlsx2md
```

Optionally pass a worksheet name: `python -m xlsx2md "Sheet1"`.

The package reads `xlsx2md/xlsx2md.xlsx` by default. For tests, run from the cloned repository's parent directory:

```bash
python -m pytest xlsx2md/tests -v
```

The GitHub Actions workflow uses `PYTHONPATH` pointing at the repository's parent, preserving this package layout while running pytest from the checkout.
