# PyWebnovel

A python library for scraping webnovels and packaging them as ebooks.  It's similar to [FanFicFare](https://github.com/JimmXinu/FanFicFare), but my own personal project.

## Running Tests

Running local-only tests:

```shell
$ ./scripts/runtests.sh
```

Running "live"-only tests:

```shell
$ ./scripts/runtests.sh live
```

Running all tests:

```shell
$ ./scripts/runtests.sh all
```

_**Note:** `runtests.sh` is just a wrapper around `pytest` and any arguments passed to `runtests.sh` (other than the "live" or "all" args in the examples above) will be passed directly to `pytest`. For example, the following would work:_

```shell
$ ./scripts/runtests.sh tests/test_events.py
```

## License

PyWebnovel is licensed under the MIT license.
