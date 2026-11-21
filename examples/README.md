# Examples

These examples are standalone scripts, not part of the installed package.
They need packages that are intentionally not mandatory runtime dependencies:

```sh
# InMemory example
python -m pip install "fastapi-cache-stable" uvicorn

# Redis example

python -m pip install "fastapi-cache-stable[redis]" uvicorn
```

To see **the same FastAPI app before and after migrating from `fastapi-cache2`**,
run the [one-command migration demo](migration/README.md). It installs the two
distributions in separate temporary virtual environments and compares safe
default behavior, without touching any Redis instance.

Run from the repository root, for example:

```sh
python examples/in_memory/main.py
```

The library itself does not require `uvicorn`; install it only when running
these scripts or your own server entry point.
