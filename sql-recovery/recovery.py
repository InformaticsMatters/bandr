#!/usr/bin/env python

"""A simple module to recover a backup.

Expects Python 3 (recursive glob).

The backup directory (BACKUP_ROOT_DIR) is expected to have
been mounted as a volume in the container image.

Recovery supports PostgreSQL backups.

When complete the content of the termination log (/dev/termination-log)
will start with either SUCCESS or FAILURE.

A number of environment variables control this utility: -

-   FROM_BACKUP

    The timestamp. This can be the ISO-8601 portion of
    the original backup filename, 'NONE' or 'LATEST'.
    The provided string is converted to upper-case.
    If 'NONE' the recovery module simply displays
    all the backups on the backup volume.
    If 'LATEST' then the latest backup file on the volume
    is used to recover the database from. If
    a time is used the file whose name matches the
    provided time will be used as a source of the recovery.
    (default 'NONE')

Variables relating to extended features...

-   DATABASE

    If set only this database will be restored.
    If undefined a complete recovery of the server (all databases)
    will be performed.

-   DATABASE_EXPECTED_COUNT

    If set, once recovery has been successful, the recovery logic
    counts the number of databases that have been recovered. If the
    actual count differs from the value of 'DATABASE_EXPECTED_COUNT'
    the recovery is considered to have failed.

    Used primarily for automated recovery tests.

Variables for PostgreSQL recovery...

-   PGHOST

    The Postgres database Hostname.
    (default '')

-   PGUSER

    The Postgres database User.
    (default 'postgres')

-   PGADMINPASS

    If you have not provided your own .pgpass file but
    want to replace the default password used in the
    built-in .pgpass file then set the password as this
    variable's value. The password will be written to
    the default .pgpass file before the recovery begins.
    (default '-')

Alan Christie
Informatics Matters
February 2021
"""

from datetime import datetime
import glob
import os
import subprocess
import sys

ERROR_NO_ROOT = 4
ERROR_NO_MSPASS = 13

# Supported database flavours...
FLAVOUR_POSTGRESQL = 'postgresql'

# Alternatives for Backup
B_NONE = 'NONE'
B_LATEST = 'LATEST'

# The backup time (NONE by default).
# This is the time from the backup filename,
# i.e. '2018-06-25T21:05:07Z'
FROM_BACKUP = os.environ.get('FROM_BACKUP', 'LATEST').upper()
# A specific database?
DATABASE = os.environ.get('DATABASE', '')
# Expected count of databases (after recovery)
DATABASE_EXPECTED_COUNT = os.environ.get('DATABASE_EXPECTED_COUNT', '')
# Extract configuration from the environment.
# Postgres material...
PGHOST = os.environ.get('PGHOST', '')
PGUSER = os.environ.get('PGUSER', 'postgres')
PGADMINPASS = os.environ.get('PGADMINPASS', '-')
HOME = os.environ['HOME']

# The backup config.
# The root dir, below which you're likely to find
# hourly, daily, weekly and monthly backup directories.
BACKUP_ROOT_DIR = '/backup'
BACKUP_FILE_PREFIX = 'backup'

# Recovery commands for the various database flavours...
RECOVERY_COMMANDS = {
    FLAVOUR_POSTGRESQL: 'psql -q -h %s -U %s -v ON_ERROR_STOP=1'
                        ' -f dumpall.sql'
                        ' > sql.out' % (PGHOST, PGUSER)
}
# Recovery commands (for a single database).
# Check comments above in case they're relevant here.
RECOVERY_COMMANDS_ONE_DB = {
    FLAVOUR_POSTGRESQL: 'psql -q -h %s -U %s -f dumpall.sql %s'
                        ' > sql.out' % (PGHOST, PGUSER, DATABASE)
}

# What 'flavour' of database do we expect to recover?
# We currently support Postgres.
# The flavour is determined by the environment variables that we find.
# If PGHOST has been defined then we'll expect a Postgres database
DATABASE_FLAVOUR = FLAVOUR_POSTGRESQL
if DATABASE:
    RECOVERY_CMD = RECOVERY_COMMANDS_ONE_DB[DATABASE_FLAVOUR]
else:
    RECOVERY_CMD = RECOVERY_COMMANDS[DATABASE_FLAVOUR]

# Units for bytes, KBytes etc.
# Used in pretty_size() and expected to be the base-10 units
# not the base 2 - i.e GBytes rather han GiBytes.
SCALE_UNITS = ['', 'K', 'M', 'G', 'T']


def write_termination_message(message='SUCCESS'):
    """Writes the message to '/dev/termination-log'.
    It's expected to be a short phrase that's written to '/dev/termination-log'
    that's available to Kubernetes once the container's finished.

    To simplify automation the message must begin 'SUCCESS' or 'FAILURE'
    the default, as clearly shown, is SUCCESS.
    """
    with open('/dev/termination-log', 'wt') as t_log_file:
        t_log_file.write(message)


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


def error(error_no):
    """Issues an error line (debug information will already be present
    on earlier log lines) and then exits with a SUCCESS code (to
    prevent OpenShift restarting the container).

    The method does not return.

    :param error_no: An error number (ideally unique for each error)
    :type error_no: ``int``
    """
    print('--] Encountered unrecoverable ERROR [%s] ... leaving' % error_no)
    write_termination_message('FAILURE (%s)' % error_no)
    sys.exit(0)


# Echo configuration...
print('# DATABASE_FLAVOUR = %s' % DATABASE_FLAVOUR)
print('# FROM_BACKUP = %s' % FROM_BACKUP)
if DATABASE:
    print('# DATABASE = %s' % DATABASE)
else:
    print('# DATABASE = (unspecified - recovering all)')
if DATABASE_EXPECTED_COUNT:
    print('# DATABASE_EXPECTED_COUNT = %s' % DATABASE_EXPECTED_COUNT)
else:
    print('# DATABASE_EXPECTED_COUNT = (unspecified)')
HAVE_ADMIN_PASS = False
if DATABASE_FLAVOUR in [FLAVOUR_POSTGRESQL]:
    print('# PGHOST = %s' % PGHOST)
    print('# PGUSER = %s' % PGUSER)
    msg = '(not supplied)'
    if PGADMINPASS not in ['-']:
        HAVE_ADMIN_PASS = True
        msg = '(supplied)'
    print('# PGADMINPASS = %s' % msg)

# Recover...
#
# 1. Check that the root backup directory exists
# 2. Display all backups
# 3. If BACKUP_FROM is 'NONE'
#       Leave
# 4.  If BACKUP_FROM is 'LATEST'
#       use the most recent backup
#    Else recover the named backup from a file whose name
#       matches the provided string, normally an ISO8601 datetime string.
#        a date and time (i.e. '2018-06-25T21:05:07Z')
# 5. Once recovery is complete, if DATABASE_EXPECTED_COUNT is set
#    we make suer that actual number of databases matches the
#    supplied value

RECOVERY_START_TIME = datetime.now()
print('--] Hello [%s]' % RECOVERY_START_TIME)
#####
# 1 #
#####
if not os.path.isdir(BACKUP_ROOT_DIR):
    print('--] Backup root directory does not exist (%s). Leaving.' % BACKUP_ROOT_DIR)
    error(ERROR_NO_ROOT)

#####
# 2 #
#####
# If postgreSQL do we replace the 'default' .pgpass?
# If the user's supplied a password using PGADMINPASS
# then replace the current (default) .pgapss file with
# with a single wildcard line using the supplied value.
if DATABASE_FLAVOUR in [FLAVOUR_POSTGRESQL] and HAVE_ADMIN_PASS:
    pgpass_file_name = '%s/.pgpass' % HOME
    print('--] Replacing "%s" (Admin password supplied)' % pgpass_file_name)
    pgpass_file = open(pgpass_file_name, 'w')
    password_entry = '*:*:*:*:%s' % PGADMINPASS
    pgpass_file.write(password_entry)
    pgpass_file.close()
# A dictionary of backup files and their directories.
LATEST_BACKUP = None
KNOWN_BACKUPS = {}
FILE_SEARCH = os.path.join(BACKUP_ROOT_DIR, '**', BACKUP_FILE_PREFIX + '*')
BACKUPS = glob.glob(FILE_SEARCH)
for BACKUP in BACKUPS:
    FILENAME = os.path.basename(BACKUP)
    DIRECTORY = os.path.dirname(BACKUP)
    if FILENAME not in KNOWN_BACKUPS:
        KNOWN_BACKUPS[FILENAME] = DIRECTORY
print('--] Known backups, most recent first (%s)...' % len(KNOWN_BACKUPS))
if KNOWN_BACKUPS:
    TOTAL_BACKUP_SIZE = 0
    for KNOWN_BACKUP in sorted(KNOWN_BACKUPS, reverse=True):
        BACKUP_SIZE = os.path.getsize(os.path.join(KNOWN_BACKUPS[KNOWN_BACKUP], KNOWN_BACKUP))
        TOTAL_BACKUP_SIZE += BACKUP_SIZE
        print('    %s (%s)' % (KNOWN_BACKUP, pretty_size(BACKUP_SIZE)))
        if not LATEST_BACKUP:
            LATEST_BACKUP = KNOWN_BACKUP
    print('--] All backups occupy %s' % pretty_size(TOTAL_BACKUP_SIZE))
else:
    print('    None')
print('--] Latest backup: %s' % LATEST_BACKUP)

#####
# 3 #
#####
if FROM_BACKUP in [B_NONE]:
    print('--] FROM_BACKUP is NONE. Nothing to do.')
    write_termination_message()
    sys.exit(0)

#####
# 4 #
#####
if not LATEST_BACKUP:
    print('--] Asked to recover LATEST but there are no backups. Sorry.')
    write_termination_message('FAILURE (No Backups)')
    sys.exit(0)

BACKUP_FILE = None
if FROM_BACKUP in [B_LATEST]:
    print('--] Attempting to recover from LATEST backup')
    BACKUP_FILE = os.path.join(KNOWN_BACKUPS[LATEST_BACKUP], LATEST_BACKUP)
else:
    print('--] Attempting to recover from %s backup' % FROM_BACKUP)
    # Search the known back keys.
    for KNOWN_BACKUP in KNOWN_BACKUPS:
        if FROM_BACKUP in KNOWN_BACKUP:
            BACKUP_FILE = os.path.join(KNOWN_BACKUPS[KNOWN_BACKUP], KNOWN_BACKUP)
            break
if not BACKUP_FILE:
    print('--] Could not find the backup. Leaving.')
    write_termination_message('FAILURE (Backup not found)')
    sys.exit(0)

# Unpack the backup to reveal the SQL
# and then use this file in the recovery command.
print('--] Recovering from %s...' % BACKUP_FILE)

# Unpack - To avoid errors relating to changing the postgres user
#          remove anything that relates to creating or dropping postgres
UNPACK_CMD = "gunzip -c %s" \
             " | egrep -v '^(CREATE|DROP) ROLE postgres;'" \
             " > dumpall.sql" % BACKUP_FILE
print("    $", UNPACK_CMD)
COMPLETED_PROCESS = subprocess.run(UNPACK_CMD, shell=True, stderr=subprocess.PIPE)

# Check subprocess exit code and stderr
if COMPLETED_PROCESS.returncode != 0 or COMPLETED_PROCESS.stderr:
    print('--] Unpack failed (returncode=%s)' % COMPLETED_PROCESS.returncode)
    if COMPLETED_PROCESS.stderr:
        print('--] stderr follows...')
        print(COMPLETED_PROCESS.stderr.decode("utf-8").strip())
    # Remove the current backup
    os.remove(BACKUP)
    print('--] Leaving')
    write_termination_message('FAILURE (Unpack failed)')
    sys.exit(0)

print("    $", RECOVERY_CMD)
COMPLETED_PROCESS = subprocess.run(RECOVERY_CMD, shell=True, stderr=subprocess.PIPE)

RECOVERY_END_TIME = datetime.now()
print('--] Recovery finished [%s]' % RECOVERY_END_TIME)
ELAPSED_TIME = RECOVERY_END_TIME - RECOVERY_START_TIME
print('--] Elapsed time %s' % ELAPSED_TIME)

# Check subprocess exit code and stderr
# We should treat stderr as a warning if the exit code is zero.
if COMPLETED_PROCESS.stderr:
    print('--] Warning, lines written to stderr')
    print('--] stderr follows...')
    print(COMPLETED_PROCESS.stderr.decode("utf-8"))

if COMPLETED_PROCESS.returncode != 0:
    print('--] Recovery failed (returncode=%s)' % COMPLETED_PROCESS.returncode)
    if not COMPLETED_PROCESS.stderr:
        print('--] There was nothing on stderr')
    print('--] Leaving (SQL can be found in dumpall.sql)')
    write_termination_message('FAILURE (Recovery failed)')
    sys.exit(0)
elif COMPLETED_PROCESS.stderr:
    print('--] Although stderr was used the recovery was successful')

#####
# 5 #
#####

# If specified then make sure it's correct.
if DATABASE_EXPECTED_COUNT:

    # Here we just get a count of the number of databases
    # and compare that with the expected value provided in
    # DATABASE_EXPECTED_COUNT.
    # If it does not match it's an error.
    COUNT_CMD = 'psql -q -h %s -U %s' \
                ' -t -c "SELECT COUNT(*) FROM pg_database;"' \
                ' | tr -d " "' % (PGHOST, PGUSER)
    CHECK_CMD = COUNT_CMD + ' | grep "^%s$"' % DATABASE_EXPECTED_COUNT
    print('--] DATABASE_EXPECTED_COUNT is set. Counting databases...')
    print('$ %s' % CHECK_CMD)
    COMPLETED_PROCESS = subprocess.run(CHECK_CMD,
                                       shell=True,
                                       stderr=subprocess.PIPE)

    if COMPLETED_PROCESS.returncode != 0:
        # Count failed.
        # Run a command to display the actual count,
        # set the termination message and then leave
        print('--] Count failed (returncode=%s)' % COMPLETED_PROCESS.returncode)
        # Display the actual count
        print('--] Expected %s but actual count is...' % DATABASE_EXPECTED_COUNT)
        COMPLETED_PROCESS = subprocess.run(COUNT_CMD,
                                           shell=True,
                                           stderr=subprocess.PIPE)
        print(COMPLETED_PROCESS.stdout.decode("utf-8"))
        write_termination_message('FAILURE (Count %s failed)' % DATABASE_EXPECTED_COUNT)
        sys.exit(0)

# Success if we get here
write_termination_message()

print('--] Done')
