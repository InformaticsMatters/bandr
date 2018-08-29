# Backup and Recovery container images
This project contains a backup container image definition that can be
used as OpenShift `CronJob` processes to backup using configurable hourly,
daily, weekly and monthly strategies.

There is also a recovery image definition that can be used as an OpenShift
`Job` in order to list and/or recover the latest backup or a specific
backup.

The images support PostgreSQL and MySQL databases, controlled by
environment variables.

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

## Command-line tests
You could run something like this from the command-line
to collect a MySQL backup in `/tmp`: -

    $ docker run -e MSHOST=172.17.0.1 \
        -e MSUSER=root -e MSPASS=my-secret-pw \
        -v /tmp:/backup informaticsmatters/sql-backup:latest

>   `172.17.01` is typically the default host in the Docker network and MySQL
    must be listening on this host (see `MYSQL_ROOT_HOST`)
    
And this to recover the latest backup: -

    $ docker run -e MSHOST=172.17.0.1 \
        -e MSUSER=root -e MSPASS=my-secret-pw \
        -v /tmp:/backup informaticsmatters/sql-recovery:latest
 