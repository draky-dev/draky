![ci status of main branch](https://github.com/draky-dev/draky/actions/workflows/main.yml/badge.svg?branch=main)

# Intro

draky is an easy to use local development tool for managing environments that's designed to make
them as transparent and customizable as possible. The tool was made to make direct work with docker
easier, instead of hiding environment configuration behind opaque layers of abstraction.

Documentation is available at [https://draky.dev](https://draky.dev).

# Tips for developing `draky`:
You don't need to rebuild `draky` to test every core change. You can start draky with
`DRAKY_MOUNT_CORE=<absolute path to the "core" directory in this repo>` environmental variable set.
It will make draky mount this directory as its core, so effectively you will be able to change
draky's core live.

Note: For `DRAKY_MOUNT_CORE` variable to take effect you need to make sure draky's core doesn't run
already. If that's the case, you can destroy it with `draky core destroy`.

Example command to run in the repository's root to mount the core directly from the repository:

```sh
draky core destroy # We make sure that the core is not already running.
DRAKY_MOUNT_CORE="$(pwd)/core" draky core start
```

# Requirements:
- bash
- docker