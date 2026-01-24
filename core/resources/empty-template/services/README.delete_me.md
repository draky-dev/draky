**Note**: This document contains only some examples of `draky`'s features to make getting started easier.
For more information, please refer to the official documentation. This file should be deleted after
configuring your service because it may become outdated.


In this directory, you can store definitions of all your services. It's up to you how you organize
them.

If you want to have a `database` service, you may want to put its configuration in a directory
named after its implementation, like `postgresql`. Then in a recipe, you can reference this service
like this:

```yaml
services:
  database:
    extends:
      file: ../../services/postgresql/services.yml
      service: postgres
```

And here is an example of a `.draky/services/postgresql/services.yml`:
```yaml
services:
  postgres:
    image: postgres
```

Note that the service name in the recipe is `database` but it extends the specific implementation
named `postgres`. For all practical purposes you will be interacting with the service as `database`.
But this distinction makes it easier to switch between different implementations.

# Example file structure of a service

The structure of the service directory is fluid. For `draky` it doesn't matter where commands,
resources and variables are stored. Commands and variables are pulled from everywhere in the
`.draky` directory; resources are referenced as volumes in the service definition.
However, this is a good example of what it could look like:

```
service_a/
  commands/
    command1.dk.sh
    command2.service_a.dk.sh
  resources/
    override/
  dk.yml <- Here you can store variables used in the services.yml file for easier customization.
  services.yml
```

## service_a/
Is the main directory of the service. It's a good practice to name it after the image used.

## commands/
In `commands/` subdirectory you can store your commands. Commands are simple shell script files. Provided they follow the correct naming scheme, they will be picked up and available in `draky`'s CLI. Available name schemes are:
 - `*.dk.sh` - if the command should be run on the host.
 - `*.[service].dk.sh` - if the command should be run in the service's container.

There is more to. For example, you can make a command run as the specific user.

You can read about all the features in the official docs.

## resources/
You can put resources used by your service here. If you use `draky-entrypoint` addon, it's
recommended that you put your filesystem overrides in the `override/` subdirectory here.

## dk.yml
Here, you can declare environmental variables that will be available in the service definition. 
That way, you can separate the important and often overriden values from the less important ones.

**Note:** Environment variables are global and available project-wide, so it's a good idea to
prefix them with the service name.

Example `dk.yml` file:
```yaml
variables:
  MYSERVICE_DB_HOST: "database"
```

There is much more to the variables that you can learn about in the official docs.

## services.yml
Here you can store the definition of your service that will be included in your master `docker-compose.yml`.

**Note:** Paths in the `volumes` value are relative to your service directory location,
which means that if you need to mount a subdirectory from the `resources/` directory, you can use:
```
volumes:
- "./resources/something:/something:cached,ro"
```

`draky` will translate them when compiling the final `docker-compose.yml` file. This is one of its
features: allowing service definitions to be encapsulated in their own directories.
