# Backup and Recovery container images

![build](https://github.com/InformaticsMatters/bandr/workflows/build/badge.svg)

![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/informaticsmatters/bandr)

[![CodeFactor](https://www.codefactor.io/repository/github/informaticsmatters/bandr/badge)](https://www.codefactor.io/repository/github/informaticsmatters/bandr)

This project contains a backup container image definition that can be
used as Kubernetes `CronJob` jobs to backup using configurable hourly,
daily, weekly and monthly strategies.

There is also a recovery image definition that can be used as an OpenShift
`Job` in order to list and/or recover the latest backup or a specific
backup.

The images support PostgreSQL and MySQL databases, controlled by
environment variables.

Both images are available on the Docker hub.

>   The image is built with PostgreSQL 13.

>   Backup does not work for MySQL 8 at the moment. In MySQL 8.0,
    **caching_sha2_password** is the default authentication plugin
    rather than **mysql_native_password**. See
    https://stackoverflow.com/questions/49963383/authentication-plugin-caching-sha2-password

>   For a detailed description of each utility refer to `backup.py` or
    `recovery.py`, where the operation and supported environment variables
    are explained.

Assuming you've logged into Docker hub you can build and push the
**latest** backup image with the following command from the `sql-backup`
directory: -

    $ docker-compose build
    $ docker-compose push
    
Build the **stable** image with: -

    $ IMAGE_TAG=stable docker-compose build
    $ IMAGE_TAG=stable docker-compose push

## Command-line tests (MySQL)
You could start a simple MySQL 5.7 docker container with: -

    $ docker run -e MYSQL_ROOT_PASSWORD=my-secret-pw \
        -e MYSQL_ROOT_HOST=172.17.0.1 -p 3306:3306 -d mysql:5.7.23
 
You could run something like this from the command-line
to collect a MySQL backup in `/tmp`: -

    $ docker run -e MSHOST=172.17.0.1 \
        -e MSUSER=root -e MSPASS=my-secret-pw \
        -v /tmp:/backup informaticsmatters/sql-backup:latest

>   `172.17.01` is typically the default host in the Docker network and MySQL
    must be listening on this host (see `MYSQL_ROOT_HOST`)
    
Use this to recover the latest backup: -

    $ docker run -e MSHOST=172.17.0.1 \
        -e MSUSER=root -e MSPASS=my-secret-pw \
        -v /tmp:/backup informaticsmatters/sql-recovery:latest
 