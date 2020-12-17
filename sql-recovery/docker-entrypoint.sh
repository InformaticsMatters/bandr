#!/usr/bin/env bash

# Is S3 the source?
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
  # And then mount the bucket to '/data'
  mkdir -p /backup
  s3fs "${AWS_BUCKET_NAME}" /backup -o passwd_file="${HOME}/.passwd-s3fs"
fi

# Run the recovery logic
./recovery.py
