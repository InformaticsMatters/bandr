#!/usr/bin/env bash

# Is S3 the destination?
if [ -v BACKUP_VOLUME_IS_S3 ]; then
  # S3 is the backup destination
  # (see https://github.com/s3fs-fuse/s3fs-fuse)
  #
  # We'll use s3fs to mount the bucket so it can be used
  # as a conventional file-system.
  # Let's put AWS credentials in a custom passwd file...
  echo "--] Backup volume is S3"

  : "${AWS_ACCESS_KEY_ID?Need to set AWS_ACCESS_KEY_ID}"
  : "${AWS_SECRET_ACCESS_KEY?Need to set AWS_SECRET_ACCESS_KEY}"

  echo "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" > "${HOME}/.passwd-s3fs"
  chmod 600 "${HOME}"/.passwd-s3fs

  # Any extra S3 args required?
  # i.e. is BACKUP_VOLUME_S3_URL or BACKUP_VOLUME_S3_REQUEST_STYLE defined?
  EXTRA_OPTIONS=""
  if [ -n "$BACKUP_VOLUME_S3_URL" ]; then
    EXTRA_OPTIONS+=" -o url=${BACKUP_VOLUME_S3_URL}"
  fi
  if [ -n "$BACKUP_VOLUME_S3_REQUEST_STYLE" ]; then
    EXTRA_OPTIONS+=" -o ${BACKUP_VOLUME_S3_REQUEST_STYLE}"
  fi

  # And then mount the bucket to '/data'
  echo "--] s3fs AWS_BUCKET_NAME=${AWS_BUCKET_NAME}"
  echo "--] s3fs EXTRA_OPTIONS=${EXTRA_OPTIONS}"
  mkdir -p /backup
  s3fs "${AWS_BUCKET_NAME}" /backup -o passwd_file="${HOME}/.passwd-s3fs ${EXTRA_OPTIONS}"
fi

# Run the backup logic
./backup.py
