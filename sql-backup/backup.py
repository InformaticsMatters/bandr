#!/usr/bin/env python

"""A simple module to create and manage backups.

The image also has additional rsync capability so that the backup directory,
at the end of each hourly run synchronises the backup volume
with a user-designated remote volume.

The backup directory (BACKUP_ROOT_DIR) is expected to have been mounted
as a volume in the container image. Without this volume the backup will exit
cleanly but with an error.

To avoid continually re-spawning nothing causes this container image
to return a non-zero exit code.

See https://www.postgresql.org/docs/9.2/static/app-pg-dumpall.html

The backup files are named according to the following format: -

    <BACKUP_FILE_PREFIX>-<ISO-8601-DATETIME>-<BACKUP_LIVE_FILE>

For example: -

    backup-2018-06-25T21:05:07Z-dumpall.sql.gz

The time of the backup is the approximate time this utility is executed,
and is the approximate time of the start of the backup process. If the backup
starts at 10:00 and takes 3 hours the backup time will be 10:00, not 13:00.

When complete the content of the termination log (/dev/termination-log)
will start with the word 'SUCCESS' or 'FAILURE'.

A number of environment variables control this image's behaviour: -

-   BACKUP_TYPE

    The type of backup. There are a number of pre-defined
    types: - 'hourly', 'daily', 'weekly' and 'monthly'.
    The 'hourly' is special in that it is the only backup
    that generates new files, the other types simply
    copy files to daily, weekly or monthly directories.
    Backup files are written to directories that match
    the type, i.e. /backup/daily. A description
    of each type can be found below.
    (default 'hourly')

-   BACKUP_COUNT

    The number of backup files to maintain for the given
    backup type.
    (default '24')

-   BACKUP_PRIOR_TYPE

    The prior backup type (i.e. the type to copy from).
    It can be one of 'daily', 'weekly', 'monthly'.
    A 'weekly' BACKUP_TYPE would normally have a
    'daily' BACKUP_PRIOR_TYPE. It is used to decide
    where to get this backup's backup files from.
    Used only if BACKUP_TYPE is not 'hourly'.
    (default 'hourly')

-   BACKUP_PRIOR_COUNT

    For types other than 'hourly' this is the number of
    backup files in the prior backup type that
    represent a 'full' set. When the prior backup directory
    contains this number of files the oldest is copied to
    this backup directory. i.e. if this is a 'weekly'
    backup and the prior type is 'daily' and you are
    collecting '6' daily files a weekly file will be
    created form the oldest daily directory when there are
    '24' files in the hourly directory. This is designed
    to prevent a backup form, copying a prior file until
    there are sufficient prior files.
    Used only if BACKUP_TYPE is not 'hourly'.
    (default '24')

-   BACKUP_PRE_EXIT_SLEEP_M

    If set, this is the time (in minutes) that the
    container image sleeps for before exiting.
    It is used for debug purposes to allow entry into the
    container or for rsync testing purposes. The
    default value is '0' which means the container
    exits immediately after completing the backup.
    (default '0')

Variables relating to extended features...

-   DATABASE

    If set only this database will be backed-up.
    If undefined a complete backup of the server (all databases)
    will be performed.

Variables for PostgreSQL backups...

-   PGHOST

    The Postgres database Hostname.
    Used only for 'hourly' backup types
    (default ''). You must define
    PGHOST for PostgreSQL backups.

-   PGUSER

    The Postgres database User.
    Used only for 'hourly' backup types
    (default 'postgres')

-   PGPASSFILE

    If you have suplied your own '.pgpass' file
    and have not placed it in the default location
    set the value of this varibale to the path and file.
    i.e. "/mydirectory/.pgpass". If you redirect the file
    using PGADMINPASS is pointless.
    (default '${HOME}/.pgpass')

-   PGADMINPASS

    If you have not provided your own .pgpass file but
    want to replace the default password used in the
    built-in .pgpass file then set the password as this
    variable's value. The password will be written to
    the default .pgpass file before the backup begins.
    If you use this variable using PGPASSFILE is pointless.
    (default '-')

Variables for (AWS) S3 backup (synchronisation).
If the AWS_BUCKET_NAME is set the code assumes that the bucket is mapped
to the expected backup mount point (BACKUP_ROOT_DIR) by the
'docker-entrypoint.sh' script, which is achieved using 's3fs'.

If you are using S3 you must not mount a backup directory at '/backup'
as the underlying 'docker-entrypoint.sh' script will do this for you and
any existing backup directory may cause an error or at the very least confusion.

-   AWS_BUCKET_NAME

    If set, it's the name of an AWS S3 bucket (default '').
    If set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set.

-   AWS_ACCESS_KEY_ID

    The access key ID for write-access to the named bucket.
    This must be set if AWS_BUCKET_NAME is set.

-   AWS_SECRET_ACCESS_KEY

    The secret access key.
    This must be set if AWS_BUCKET_NAME is set.

If the backup volume is S3-based (i.e. you expect docker-entrypoint.sh to
mount an S3 volume) then you need to set a number of variables: -

-   BACKUP_VOLUME_IS_S3

    Set to anything (typically 'yes') in order to mount an S3 volume
    into the backup destination ('/backup').

-   BACKUP_VOLUME_S3_URL

    If you use s3fs with a non-Amazon S3 implementation,
    provide the URL (i.e. 'https://url.to.s3/') here.
    This is used in the docker-entrypoint when setting-up s3fs.

-   BACKUP_VOLUME_S3_REQUEST_STYLE

    If you use s3fs with a non-Amazon S3 implementation,
    you can use this to provide path-style requests.
    i.e. set to 'use_path_request_style' if required.
    This is used in the docker-entrypoint when setting-up s3fs.

    This is actually passed to s3fs as a '-o' command-line option
    so it could be any valid option.

Variables for rsync remove copying support.
If the RSYNC_HOST variable is set each successful hourly backup
will result in an rsync of the backup volume to
a remotely location designated by the related environment variables.

-   RSYNC_HOST

    The hostname of the rsync destination.
    If set backups are synchronised to this server in the directory
    identified by RSYNC_TGT_PATH using the RSYNC_USER and RSYNC_PASS.
    (default unset)

-   RSYNC_USER

    The username of an rsync user.
    If set backups are synchronised to the directory.
    (default unset)

-   RSYNC_PASS

    The rsync user's password and the password used with sshpass.
    This has to be set if RSYNC_USER is set.
    (default unset)

-   RSYNC_PATH

    The rsync target path.
    (default unset)

There are four values for BACKUP_TYPE: -

- hourly    Typically the BACKUP_COUNT is 24.
            This type always starts by creating a new backup.
            It is the shortest backup period and writes to the 'hourly'
            directory. This backup is expected to be invoked hourly.
            BACKUP_PRIOR_COUNT is ignored.

- daily     This backup is configured to run once a day (at a time
            defined by the user). It copies the oldest backup from the
            'hourly' directory into the 'daily' directory but only when the
            hourly directory contains BACKUP_PRIOR_COUNT backup files
            (normally 24). It makes sure that no more than BACKUP_COUNT
            files exist in the daily directory.

- weekly    This backup is configured to run once a week (at a time
            defined by the user). It copies the oldest backup from the
            'daily' directory into the 'weekly' directory but only when the
            daily directory contains BACKUP_PRIOR_COUNT backup files
            (normally 7). It makes sure that no more than BACKUP_COUNT
            files exist in the weekly directory.

- monthly   This backup is configured to run once a month (at a time
            defined by the user). It copies the oldest backup from the
            'weekly' directory into the 'monthly' directory but only when the
            weekly directory contains BACKUP_PRIOR_COUNT backup files
            (normally 4). It makes sure that no more than BACKUP_COUNT
            files exist in the monthly directory.

How does it work? (PostgreSQL)

The backup relies on the operation of the PostgreSQL client utility `pg_dumpall`.
Given a postgres admin username (and a suitable .pgpass file) we leave
everything up to it. The command is captured in the BACKUP_CMD variable.
The resultant SQL file is then compressed with gzip. The user is then required
to set the environment variables appropriately and run the container image regularly
(as A CronJob in OpenShift).

For simple deployment, where one admin password is sufficient, you can define the
database administrator password as an environment variable (PGADMINPASS). The backup
utility will replace the value in its built-in .pgpass file. Alternatively,
for more complex deployments with multiple databse passwords you can replace the
.pgpass file. In OpenShift you can do this with a ConfigMap, and that might
look something like this: -

    - kind: ConfigMap
      apiVersion: v1
      metadata:
        name: postgresql-pgpass
      data:
        .pgpass: |
          *:*:*:*:${DB_ADMIN_PASSWORD}

Then, to use that in your backup container, replacing the default .pgpass file,
you simply define volumes and volumeMounts for the ConfigMap. A bit like this: -

    containers:
    - image: informaticsmatters/postgresql-backup:stable
      [...]
      volumeMounts:
      - name: pgpass
        mountPath: /root/.pgpass
        subPath: .pgpass
    volumes:
    - name: pgpass
      configMap:
        name: postgresql-pgpass
        defaultMode: 0600

A termination message (success or failure) is written to the file defined
by TERMINATION_LOG (i.e. /dev/termination-log, the default location expected
by Kubernetes).

Alan Christie
Informatics Matters
February 2021
"""

import glob
import os
import sys
import subprocess
import shutil
import time
from datetime import datetime

TERMINATION_LOG = '/dev/termination-log'

ERROR_NO_PGPASS = 1
ERROR_UNEXPECTED_BU_TYPE = 2
ERROR_UNEXPECTED_PBU_TYPE = 3
ERROR_NO_ROOT = 4
ERROR_BU_ERROR = 5
ERROR_NO_BU = 6
ERROR_MKDIR = 7
ERROR_REMOVE = 8
ERROR_BACKUP_COPY = 9
ERROR_REMOVE_COPY = 10
ERROR_REMOVE_EXPIRED = 11
ERROR_REMOVE_OLDEST = 12
ERROR_NO_MSPASS = 13
ERROR_MISSING_RSYNC_USER = 14
ERROR_MISSING_RSYNC_PASS = 15
ERROR_MISSING_RSYNC_PATH = 16
ERROR_RSYNC_FAILED = 17
ERROR_KEYSCAN_FAILED = 18
ERROR_MISSING_AWS_CREDENTIALS = 19
ERROR_FAILED_DELETING_BUCKET_OBJECT = 20
ERROR_INCOMPLETE_AWS = 21

# Hide the backup/rsync commands?
HIDE_BACKUP_COMMAND = False
HIDE_RSYNC_COMMAND = True

# Supported database flavours...
FLAVOUR_POSTGRESQL = 'postgresql'

# Backup types...
B_HOURLY = 'hourly'
B_DAILY = 'daily'
B_WEEKLY = 'weekly'
B_MONTHLY = 'monthly'

# The backup type is HOURLY by default.
# Hourly backups always create a new backup and limit
# the count to 24 (by default).
BACKUP_TYPE = os.environ.get('BACKUP_TYPE', B_HOURLY).lower()
BACKUP_COUNT = int(os.environ.get('BACKUP_COUNT', '24'))
BACKUP_PRIOR_TYPE = os.environ.get('BACKUP_PRIOR_TYPE', B_HOURLY).lower()
BACKUP_PRIOR_COUNT = int(os.environ.get('BACKUP_PRIOR_COUNT', '24'))
BACKUP_PRE_EXIT_SLEEP_M = int(os.environ.get('BACKUP_PRE_EXIT_SLEEP_M', '0'))
# A specific database?
DATABASE = os.environ.get('DATABASE', '')
# Extract configuration from the environment.
# Postgres material...
PGHOST = os.environ.get('PGHOST', '')
PGUSER = os.environ.get('PGUSER', 'postgres')
PGPASSFILE = os.environ.get('PGPASSFILE', '${HOME}/.pgpass')
PGADMINPASS = os.environ.get('PGADMINPASS', '-')
HOME = os.environ['HOME']
# AWS S3 material...
# If the bucket name is used we assume
# the AWS environment variables are also set
AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME', '')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
# RSYNC configuration
RSYNC_HOST = os.environ.get('RSYNC_HOST', '')
RSYNC_USER = os.environ.get('RSYNC_USER', '')
RSYNC_PASS = os.environ.get('RSYNC_PASS', '')
RSYNC_PATH = os.environ.get('RSYNC_PATH', '')

# The backup config.
# The root dir, below which you're likely to find
# hourly, daily, weekly and monthly backup directories.
BACKUP_ROOT_DIR = '/backup'
BACKUP_LIVE_FILE = 'dumpall.sql.gz' # The new file
BACKUP_FILE_PREFIX = 'backup'       # Prefix for older files

BACKUP_PRIOR_DIR = os.path.join(BACKUP_ROOT_DIR, BACKUP_PRIOR_TYPE)
BACKUP_DIR = os.path.join(BACKUP_ROOT_DIR, BACKUP_TYPE)
BACKUP = os.path.join(BACKUP_DIR, BACKUP_LIVE_FILE)

# Backup commands (for all databases) for the various database flavours...
BACKUP_COMMANDS = {
    FLAVOUR_POSTGRESQL: 'pg_dumpall --username=%s --no-password --clean --if-exists'
                        ' | gzip > %s' % (PGUSER, BACKUP)
}
# Backup commands (for a single database).
# Check comments above in case they're relevant here.
BACKUP_COMMANDS_ONE_DB = {
    FLAVOUR_POSTGRESQL: 'pg_dump --username=%s --no-password --clean --if-exists %s'
                        ' | gzip > %s' % (PGUSER, DATABASE, BACKUP)
}

# What 'flavour' of database do we expect to be backing up?
# The flavour is determined by the environment variables that we find.
# If PGHOST has been defined then we'll expect a Postgres database
#
# This really only applies to B_HOURLY backups, as that's the only
# type that actually creates new backup files.
DATABASE_FLAVOUR = FLAVOUR_POSTGRESQL
if DATABASE:
    BACKUP_CMD = BACKUP_COMMANDS_ONE_DB[DATABASE_FLAVOUR]
else:
    BACKUP_CMD = BACKUP_COMMANDS[DATABASE_FLAVOUR]

# Units for bytes, KBytes etc.
# Used in pretty_size() and expected to be the base-10 units
# not the base 2 - i.e GBytes rather han GiBytes.
SCALE_UNITS = ['', 'K', 'M', 'G', 'T']

# Echo configuration...
HAVE_ADMIN_PASS = False
print('# DATABASE_FLAVOUR = %s' % DATABASE_FLAVOUR)
print('# BACKUP_TYPE = %s' % BACKUP_TYPE)
print('# BACKUP_COUNT = %s' % BACKUP_COUNT)
print('# BACKUP_DIR = %s' % BACKUP_DIR)
if BACKUP_TYPE not in [B_HOURLY]:
    print('# BACKUP_PRIOR_TYPE = %s' % BACKUP_PRIOR_TYPE)
    print('# BACKUP_PRIOR_COUNT = %s' % BACKUP_PRIOR_COUNT)
print('# BACKUP_PRE_EXIT_SLEEP_M = %s' % BACKUP_PRE_EXIT_SLEEP_M)
if DATABASE:
    print('# DATABASE = %s' % DATABASE)
else:
    print('# DATABASE = (unspecified - backing up all)')
if BACKUP_TYPE in [B_HOURLY]:
    if DATABASE_FLAVOUR in [FLAVOUR_POSTGRESQL]:
        print('# PGHOST = %s' % PGHOST)
        print('# PGUSER = %s' % PGUSER)
        print('# PGPASSFILE = %s' % PGPASSFILE)
        msg = '(not supplied)'
        if PGADMINPASS not in ['-']:
            HAVE_ADMIN_PASS = True
            msg = '(supplied)'
        print('# PGADMINPASS = %s' % msg)
if AWS_BUCKET_NAME:
    print('# AWS_BUCKET_NAME = %s' % AWS_BUCKET_NAME)
print('# RSYNC_HOST = %s' % RSYNC_HOST)
print('# RSYNC_PATH = %s' % RSYNC_PATH)


def pretty_size(number):
    """Returns the number as a pretty number.
    i.e. 2,971,821,278 is returned as '2.97 GBytes'

    :param number: The number
    :type number: ``Integer``
    """
    float_bytes = float(number)
    scale_factor = 0
    while float_bytes >= 1000 and scale_factor < len(SCALE_UNITS) - 1:
        scale_factor += 1
        float_bytes /= 1000
    return "{0:,.2f} {1:}Bytes".format(float_bytes, SCALE_UNITS[scale_factor])


def write_termination_message(message=None):
    """Writes the message to '/dev/termination-log'.
    It's expected to be a short phrase that's written to '/dev/termination-log'
    that's available to Kubernetes once the container's finished.

    To simplify automation tools that inspect the termination log
    the message begins 'SUCCESS' or 'FAILURE'.
    'SUCCESS' is written if the message is 'None'.
    """
    log_message = 'FAILURE (%s)' % message if message else 'SUCCESS'
    with open('/dev/termination-log', 'wt') as t_log_file:
        t_log_file.write(log_message)


def error(error_no):
    """Issues an error line (debug information will already be present
    on earlier log lines) and then exits with a SUCCESS code (to
    prevent OpenShift restarting the container).

    The method does not return.

    :param error_no: An error number (ideally unique for each error)
    :type error_no: ``int``
    """
    message = 'Encountered unrecoverable ERROR [%s] ... leaving' % error_no
    print('--] %s' % message)
    write_termination_message(error_no)
    sys.exit(0)


# Backup...
#
# 0. Check environment
# 1. Check that the root backup directory exists
#    and create a sub-directory if required
#    (remembering that the ultimate volume can be S3)
#
# For hourly backup types...
#
# 2. If the backup file exists then generate a warning
# 3. Run the backup (leaving if no backup was created)
# 4. Copy the live backup to a new prefixed date/time named file
#    and then remove the original file.
#
# For all all but hourly types...
#
# 5. Copy the oldest file from the prior backup.
#    Daily copies from Hourly, weekly copies form daily,
#    Monthly copies from weekly. This only happens if the prior count
#    is satisfied.
#
# For all backup types...
#
# 6. Limit the files in the current backup directory
#
# If it's an HOURLY backup...
#
# 7. If RSYNC_HOST is set, rsync the backup volume to
#    the named path.

BACKUP_START_TIME = datetime.now()
print('--] Hello [%s]' % BACKUP_START_TIME)

#####
# 0 #
#####
# If PostgreSQL Does the PGPASS file exist?
if DATABASE_FLAVOUR in [FLAVOUR_POSTGRESQL]:
    PGPASS_FILE = os.path.expandvars(PGPASSFILE)
    if not os.path.isfile(PGPASS_FILE):
        print('--] PGPASSFILE (%s) does not exist' % PGPASSFILE)
        error(ERROR_NO_PGPASS)
# Check backup types...
if BACKUP_TYPE not in [B_HOURLY, B_DAILY, B_WEEKLY, B_MONTHLY]:
    print('--] Unexpected BACKUP_TYPE (%s)' % BACKUP_TYPE)
    error(ERROR_UNEXPECTED_BU_TYPE)
if BACKUP_PRIOR_TYPE not in [B_HOURLY, B_DAILY, B_WEEKLY]:
    print('--] Unexpected BACKUP_PRIOR_TYPE (%s)' % BACKUP_PRIOR_TYPE)
    error(ERROR_UNEXPECTED_PBU_TYPE)

# Must have all or nothing with regard to AWS info
AWS_VAR_COUNT = 0
if AWS_BUCKET_NAME:
    AWS_VAR_COUNT += 1
if AWS_ACCESS_KEY_ID:
    AWS_VAR_COUNT += 1
if AWS_SECRET_ACCESS_KEY:
    AWS_VAR_COUNT += 1
if AWS_VAR_COUNT not in [0, 3]:
    print('--] If specifying AWS variables you must define them all')
    error(ERROR_INCOMPLETE_AWS)

#####
# 1 #
#####
if not os.path.isdir(BACKUP_ROOT_DIR):
    print('--] Backup root directory does not exist (%s)' % BACKUP_ROOT_DIR)
    error(ERROR_NO_ROOT)
if not os.path.isdir(BACKUP_DIR):
    try:
        os.makedirs(BACKUP_DIR)
    except Exception as expn:
        print('--] Exception creating backup directory (%s): -' % BACKUP_DIR)
        print('--] %s' % expn)
        error(ERROR_MKDIR)

if BACKUP_TYPE == B_HOURLY:

    # Hourly backups always create new backup files...
    #
    # Hourly backup does not have to run every hour.
    # The user can just run one each day but at least one
    # hourly backup must be run as its the only type that
    # creates backup files - the other types simply copy files
    # from the prior type.

    #####
    # 2 #
    #####
    # The corresponding CronJob template should have
    # "concurrencyPolicy: Forbid" so no two backup jobs
    # can be of the same type. Therefore, if the 'live' backup file
    # exists then we know it's here because of some catastrophic failure.
    # We warn the user but then have to continue by replacing it.
    if os.path.exists(BACKUP):
        print('--] Warning. Live backup file exists (%s). It will be replaced.' % BACKUP)

    #####
    # 3 #
    #####
    # If postgreSQL do we replace the 'default' .pgpass?
    # If the user's supplied a password using PGADMINPASS
    # then replace the current (default) .pgapss file with
    # with a single wildcard line using the supplied value.]
    if DATABASE_FLAVOUR in [FLAVOUR_POSTGRESQL] and HAVE_ADMIN_PASS:
        pgpass_file_name = '%s/.pgpass' % HOME
        print('--] Replacing "%s" (Admin password supplied)' % pgpass_file_name)
        pgpass_file = open(pgpass_file_name, 'w')
        password_entry = '*:*:*:*:%s' % PGADMINPASS
        pgpass_file.write(password_entry)
        pgpass_file.close()
    # Start the backup...
    print('--] Starting backup [%s]' % BACKUP_START_TIME)
    if not HIDE_BACKUP_COMMAND:
        print("    $", BACKUP_CMD)
    COMPLETED_PROCESS = subprocess.run(BACKUP_CMD, shell=True,
                                       stderr=subprocess.PIPE)
    BACKUP_END_TIME = datetime.now()
    print('--] Backup finished [%s]' % BACKUP_END_TIME)
    ELAPSED_TIME = BACKUP_END_TIME - BACKUP_START_TIME
    print('--] Elapsed time %s' % ELAPSED_TIME)

    # Check subprocess exit code and stderr
    if COMPLETED_PROCESS.returncode != 0 or COMPLETED_PROCESS.stderr:
        print('--] Backup failed (returncode=%s)' % COMPLETED_PROCESS.returncode)
        if COMPLETED_PROCESS.stderr:
            print('--] stderr follows...')
            print(COMPLETED_PROCESS.stderr.decode("utf-8").strip())
        # Remove the current backup
        try:
            os.remove(BACKUP)
        except Exception as expn:
            print('--] Exception removing backup (%s): -' % BACKUP)
            print('--] %s' % expn)
            error(ERROR_REMOVE)
        print('--] Backup file removed [%s]' % BACKUP)
        error(ERROR_BU_ERROR)

    # Leave if there is no backup file.
    if not os.path.isfile(BACKUP):
        print('--] No backup file was generated. Leaving')
        error(ERROR_NO_BU)

    print('--] Backup size {:,} bytes'.format(os.path.getsize(BACKUP)))

    #####
    # 4 #
    #####
    # The backup time is the start time of this job
    # (but ignore any fractions of a second and then add 'Z'
    # to be very clear that it's UTC).
    BACKUP_TIME = BACKUP_START_TIME.isoformat().split('.')[0] + 'Z'
    COPY_BACKUP_FILE = '%s-%s-%s' % (BACKUP_FILE_PREFIX,
                                     BACKUP_TIME,
                                     BACKUP_LIVE_FILE)
    print('--] Copying %s to %s...' % (BACKUP_LIVE_FILE, COPY_BACKUP_FILE))
    BACKUP_TO = os.path.join(BACKUP_DIR, COPY_BACKUP_FILE)
    try:
        shutil.copyfile(BACKUP, BACKUP_TO)
    except Exception as expn:
        print('--] Exception backup file (%s->%s): -' % (BACKUP, BACKUP_TO))
        print('--] %s' % expn)
        error(ERROR_BACKUP_COPY)
    try:
        os.remove(BACKUP)
    except Exception as expn:
        print('--] Exception removing unwanted backup file (%s): -' % BACKUP)
        print('--] %s' % expn)
        error(ERROR_REMOVE_COPY)

else:

    #####
    # 5 #
    #####
    # Daily, weekly or monthly backup...
    FILE_SEARCH = os.path.join(BACKUP_PRIOR_DIR, BACKUP_FILE_PREFIX + '*')
    EXISTING_PRIOR_BACKUPS = glob.glob(FILE_SEARCH)
    NUM_PRIOR_BACKUPS = len(EXISTING_PRIOR_BACKUPS)
    if NUM_PRIOR_BACKUPS == BACKUP_PRIOR_COUNT:
        # Prior backup has sufficient files.
        # Copy the oldest
        EXISTING_PRIOR_BACKUPS.sort()
        OLDEST_PRIOR = EXISTING_PRIOR_BACKUPS[0]
        print('--] Copying oldest %s to %s' % (BACKUP_PRIOR_TYPE, BACKUP_DIR))
        print('    %s' % OLDEST_PRIOR)
        try:
            shutil.copy2(OLDEST_PRIOR, BACKUP_DIR)
        except Exception as expn:
            print('--] Exception copying oldest backup file (%s->%s): -' % OLDEST_PRIOR, BACKUP_DIR)
            print('--] %s' % expn)
            error(ERROR_REMOVE_OLDEST)
    else:
        print('--] Nothing to do. Too few prior backups (%s)' % NUM_PRIOR_BACKUPS)

#####
# 6 #
#####
# Prune files in the current backup directory...
FILE_SEARCH = os.path.join(BACKUP_DIR, BACKUP_FILE_PREFIX + '*')
EXISTING_BACKUPS = glob.glob(FILE_SEARCH)
NUM_TO_DELETE = len(EXISTING_BACKUPS) - BACKUP_COUNT
if NUM_TO_DELETE > 0:
    print('--] Removing expired backups...')
    EXISTING_BACKUPS.sort()
    for EXISTING_BACKUP in EXISTING_BACKUPS[:NUM_TO_DELETE]:
        print('    %s' % EXISTING_BACKUP)
        try:
            os.remove(EXISTING_BACKUP)
        except Exception as expn:
            print('--] Exception removing expired backup file (%s): -' % EXISTING_BACKUP)
            print('--] %s' % expn)
            error(ERROR_REMOVE_EXPIRED)
else:
    print('--] No expired backups to delete')

UNEXPIRED_BACKUPS = glob.glob(FILE_SEARCH)
if UNEXPIRED_BACKUPS:
    print('--] Unexpired backups, most recent first (%s)...' % len(UNEXPIRED_BACKUPS))
    UNEXPIRED_BACKUPS.sort(reverse=True)
    TOTAL_BACKUP_SIZE = 0
    for UNEXPIRED_BACKUP in UNEXPIRED_BACKUPS:
        BACKUP_SIZE = os.path.getsize(UNEXPIRED_BACKUP)
        TOTAL_BACKUP_SIZE += BACKUP_SIZE
        print('    %s (%s)' % (UNEXPIRED_BACKUP, pretty_size(BACKUP_SIZE)))
    print('--] All backups occupy %s' % pretty_size(TOTAL_BACKUP_SIZE))
else:
    print('--] No unexpired backups to list')

if BACKUP_PRE_EXIT_SLEEP_M > 0:
    print('--] Sleeping (BACKUP_PRE_EXIT_SLEEP_M=%s)...' % BACKUP_PRE_EXIT_SLEEP_M)
    time.sleep(BACKUP_PRE_EXIT_SLEEP_M * 60)

#####
# 7 #
#####
# Check whether the user also wants to rsync the backup content...
if BACKUP_TYPE in [B_HOURLY] and RSYNC_HOST:

    if not RSYNC_USER:
        error(ERROR_MISSING_RSYNC_USER)
    elif not RSYNC_PASS:
        error(ERROR_MISSING_RSYNC_PASS)
    elif not RSYNC_PATH:
        error(ERROR_MISSING_RSYNC_PATH)

    # Update known_hosts
    #
    # Get the known hosts populated with the server host key.
    # See https://stackoverflow.com/questions/44337659/host-key-verification-failed-with-sshpass-rsync
    print('--] Running ssh-keyscan...')
    CMD = 'ssh-keyscan %s >> ~/.ssh/known_hosts' % RSYNC_HOST
    COMPLETED_PROCESS = subprocess.run(CMD, shell=True,
                                       stderr=subprocess.PIPE)
    if COMPLETED_PROCESS.returncode != 0:
        print('--] Keyscan failed (returncode=%s)' % COMPLETED_PROCESS.returncode)
        if COMPLETED_PROCESS.stderr:
            print('--] stderr follows...')
            print(COMPLETED_PROCESS.stderr.decode("utf-8").strip())
        error(ERROR_KEYSCAN_FAILED)
    print('--] Done')

    # rsync
    #
    # --delete ensures that any file that exists in the remote directory
    # that is no longer on the backup drive is deleted - so the target
    # is a copy of the source. If we don't delete then the target directory
    # will just accumulate backup files that we've pruned.
    RSYNC_CMD = 'rsync -Aav %s %s@%s:%s --delete' % (BACKUP_ROOT_DIR,
                                                     RSYNC_USER,
                                                     RSYNC_HOST,
                                                     RSYNC_PATH)
    RSYNC_START_TIME = datetime.now()
    print('--] Running rsync [%s]' % RSYNC_START_TIME)
    if not HIDE_RSYNC_COMMAND:
        print("    $", RSYNC_CMD)

    # Now prefix with the password details using sshpass...
    RSYNC_CMD = 'sshpass -p "%s" %s' % (RSYNC_PASS, RSYNC_CMD)
    COMPLETED_PROCESS = subprocess.run(RSYNC_CMD, shell=True,
                                       stderr=subprocess.PIPE)

    RSYNC_END_TIME = datetime.now()
    print('--] rsync finished [%s]' % RSYNC_END_TIME)
    ELAPSED_TIME = RSYNC_END_TIME - RSYNC_START_TIME
    print('--] Elapsed time %s' % ELAPSED_TIME)

    if COMPLETED_PROCESS.returncode != 0 or COMPLETED_PROCESS.stderr:
        print('--] rsync failed (returncode=%s)' % COMPLETED_PROCESS.returncode)
        if COMPLETED_PROCESS.stderr:
            print('--] stderr follows...')
            print(COMPLETED_PROCESS.stderr.decode("utf-8").strip())
        error(ERROR_RSYNC_FAILED)

# Success if we get here
write_termination_message()

print('--] Goodbye')
