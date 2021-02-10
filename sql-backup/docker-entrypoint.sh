#!/usr/bin/env bash

# BACKUP_VOLUME_IS_S3     If this is set then s3fs is employed to
#                         mount an S3 bucket, where...
# AWS_ACCESS_KEY_ID       Is the bucket access key ID
# AWS_SECRET_ACCESS_KEY   Is the bucket access secret
# AWS_BUCKET_NAME         Is the bucket name
# BACKUP_VOLUME_S3_URL            Is used for non-AWS buckets
# BACKUP_VOLUME_S3_REQUEST_STYLE  Is used for non-AWS buckets
#
# POST_DEBUG              If this is set this script stops
#                         (goes into a while loop) once the recovery is
#                         complete.

# Echo the image g_dumpall version
PG_DUMPALL_VERSION=$(pg_dumpall --version)
echo "# PG_DUMPALL_VERSION = ${PG_DUMPALL_VERSION}"

# Is S3 the destination?
if [ -v BACKUP_VOLUME_IS_S3 ]; then
  # S3 is the backup destination
  # (see https://github.com/s3fs-fuse/s3fs-fuse)
  echo "--] Backup volume is S3"

  # Certain credentials are essential...
  : "${AWS_ACCESS_KEY_ID?Need to set AWS_ACCESS_KEY_ID}"
  : "${AWS_SECRET_ACCESS_KEY?Need to set AWS_SECRET_ACCESS_KEY}"

  echo "# AWS_ACCESS_KEY_ID = (supplied)"
  echo "# AWS_SECRET_ACCESS_KEY = (supplied)"
  echo "# AWS_BUCKET_NAME = ${AWS_BUCKET_NAME}"
  echo "# BACKUP_VOLUME_S3_URL = ${BACKUP_VOLUME_S3_URL}"
  echo "# BACKUP_VOLUME_S3_REQUEST_STYLE = ${BACKUP_VOLUME_S3_REQUEST_STYLE}"
  if [ -n "${POST_DEBUG+x}" ]; then
    echo "# POST_DEBUG = (defined)"
  else
    echo "# POST_DEBUG = (not defined)"
  fi

  # We'll use s3fs to mount the bucket so it can be used
  # as a conventional file-system.
  #
  # For this process to work the container MUST run in privileged mode.
  # e.g. - if launching with the docker command
  #        you must use add the `--privileged` option.

  # Put AWS credentials in a custom passwd file...
  echo "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" > /tmp/.passwd-s3fs
  chmod 600 /tmp/.passwd-s3fs

  # Any extra S3-Fuse args required?
  # i.e. is BACKUP_VOLUME_S3_URL or BACKUP_VOLUME_S3_REQUEST_STYLE defined?
  S3FS_EXTRA_OPTIONS=""
  if [ -n "$BACKUP_VOLUME_S3_URL" ]; then
    S3FS_EXTRA_OPTIONS+="-o url=${BACKUP_VOLUME_S3_URL}"
  fi
  if [ -n "$BACKUP_VOLUME_S3_REQUEST_STYLE" ]; then
    S3FS_EXTRA_OPTIONS+=" -o ${BACKUP_VOLUME_S3_REQUEST_STYLE}"
  fi

  # Create the target directory ('/backup')
  # and then invoke s3fs
  mkdir -p /backup
  S3FS_CMD_OPTIONS="/backup -o passwd_file=/tmp/.passwd-s3fs ${S3FS_EXTRA_OPTIONS}"
  echo "--] s3fs AWS_BUCKET_NAME=${AWS_BUCKET_NAME}"
  echo "--] s3fs S3FS_CMD_OPTIONS=${S3FS_CMD_OPTIONS}"
  s3fs ${AWS_BUCKET_NAME} ${S3FS_CMD_OPTIONS}
fi

# Run the backup logic
./backup.py

# Has a POST_DEBUG been defined?
# If so then wait here - for a long time!
if [ -n "${POST_DEBUG+x}" ]; then
  echo "--] POST_DEBUG defined. Stopping..."
  while true; do
    sleep 10000
  done
else
  echo "--] POST_DEBUG is not defined - leaving now..."
fi
