#!/usr/bin/env bash

# Is S3 the source?
if [ -v BACKUP_VOLUME_IS_S3 ]; then
  # S3 is the backup destination
  # (see https://github.com/s3fs-fuse/s3fs-fuse)
  echo "--] Backup volume is S3"

  # Certain credentials are essential...
  : "${AWS_ACCESS_KEY_ID?Need to set AWS_ACCESS_KEY_ID}"
  : "${AWS_SECRET_ACCESS_KEY?Need to set AWS_SECRET_ACCESS_KEY}"

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

# Run the recovery logic
./recovery.py
