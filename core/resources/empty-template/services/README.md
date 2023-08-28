In this directory, you can store all your services.
To create a service, create a new directory, preferably, with a service's name.
In this directory, you can create a `dk.env` file. In this file you can define environment variable that you'll be able
to use in your service definition.

# Example file structure of the service
```
service_a/
  commands/
    command1.dk.sh
    command2.service_a.dk.sh
  resources/
    override/
      /etc/nginx/conf.d/website.conf
  dk.env
  local.dk.env
  services.yml
```

## service_a/
Is the main directory of the service. Its name should be your service's name.

## commands/
In `commands/` subdirectory you can store your commands. Commands are simple shell script files. Provided they have a correct naming scheme, they will be picked up and available in `draky`'s CLI. Available name schemes are:
 - `*.dk.sh` - if the command should be run on the host.
 - `*.[service].dk.sh` - if the command should be run in the service's container.

## resources/
You can put resources used by your service here. If you are using one of the `draky`'s images, it's recommended that you put your filesystem overrides in the `override/` subdirectory here.

## dk.env
Here, you can declare environmental variables that will be available in the `docker compose`'s service definition. That way, you can separate the important variables from the less important ones. Variables in this file can also be overidden easily. This file is being automatically picked up by its name.
**Note:** Environment variables should be unique project-wide, so it's a good idea to prefix them with a service name.

## local.dk.env
This is mostly the same as `dk.env`, but variables from this file override the variables from `dk.env`. This file should be gitignored to allow local customizations.

## services.yml
Here you can store the definition of your service that will be included by your master `docker-compose.yml`.
**Note:** Paths in the `volumes` value are relative to your service directory location, which means that if you need to mount a subdirectory from the `resources/` directory, you can just use:
```
volumes:
- "./resources/something:/something:cached,ro"
```
