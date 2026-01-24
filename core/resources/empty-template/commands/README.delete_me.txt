**Note**: This document contains only some examples of `draky`'s features to make getting started easier.
For more information, please refer to the official documentation. This file should be deleted after
configuring your service because it may become outdated.

Here you can put your custom commands that are not tied to any specific service.

Commands are simple shell script files. Provided they have a correct naming scheme, they will be picked up and available in `draky`'s CLI. Available name schemes are:
 - `*.dk.sh` - if the command should be run on the host. This is useful if your command uses output
   of multiple services.
 - `*.[service].dk.sh` - if the command should be run inside the service's container.

There is also a way to make a command run as a specific user inside the container. This is useful if this
command creates some files that should be owned by a non-root user.

This and more features are described in the documentation.
