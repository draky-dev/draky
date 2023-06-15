In this directory you can store your environments.

**Note**: At the moment of creating this template only the "dev" environment was supported. Check in documentation
if multiple environments are available.

Create a `dev` subdirectory and put your `docker-composer.yml` there. You can then pull services from other files
like that:

```
services:
  database:
    extends:
      file: ../../services/mariadb-alpine/services.yml
      service: mariadb
  webserver:
    extends:
      file: ../../services/webserver/services.yml
      service: webserver
    depends_on:
      - php
  php:
    extends:
      file: ../../services/php/services.yml
      service: php
  mailhog:
    extends:
      file: ../../services/mailhog/services.yml
      service: mailhog
```
