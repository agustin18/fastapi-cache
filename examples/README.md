# Examples

These examples are standalone scripts, not part of the installed package.
They need packages that are intentionally not mandatory runtime dependencies:

```sh
# InMemory example
python -m pip install "fastapi-cache-stable" uvicorn

# Redis example

python -m pip install "fastapi-cache-stable[redis]" uvicorn
```

Run from the repository root, for example:

```sh
python examples/in_memory/main.py
```

The library itself does not require `uvicorn`; install it only when running
these scripts or your own server entry point.
