Here you can put your custom commands that are not tied to any specific service.

Commands are simple shell script files. Provided they have a correct naming scheme, they will be picked up and available in `draky`'s CLI. Available name schemes are:
 - `*.dk.sh` - if the command should be run on the host.
 - `*.[service].dk.sh` - if the command should be run in the service's container.
