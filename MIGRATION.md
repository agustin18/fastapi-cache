# Migrating from fastapi-cache2

`fastapi-cache-stable` is a drop-in stable fork of `fastapi-cache2`. The Python
import is unchanged.

## Install

```sh
pip uninstall -y fastapi-cache2
pip install fastapi-cache-stable
# with extras:
pip install "fastapi-cache-stable[redis]"
```

The `fastapi_cache` import stays:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
```

Do not install both `fastapi-cache2` and `fastapi-cache-stable` in the same
environment: they provide the same `fastapi_cache` package.

## Status

This is an alpha (`0.3.0a0`) to reserve the distribution name. The 0.3.0 release
will include the P0 correctness fixes and the compatibility tests. See
`CHANGELOG.md` and `SUPPORT.md`.
