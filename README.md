# Backup And Recovery container images
This project contains a backup container image definition that can be
used as OpenShift `CronJob` processes to backup using configurable hourly,
daily, weekly and monthly strategies.

There is also a recovery image definition that can be used as an OpenShift
`Job` in order to list and/or recover the latest backup or a specific
backup.

Both images are available on the Docker hub.

>   For a detailed description of each utility refer to `backup.py` or
    `recovery.py`, where the operation and supported environment variables
    are explained.

Assuming you've logged into Docker hub you can build the **latest** image
with the following commands from the appropriate directory: -

    $ docker-compose build
    $ docker-compose push
    
And the **stable** image with: -

    $ IMAGE_TAG=stable docker-compose build
    $ IMAGE_TAG=stable docker-compose push
 