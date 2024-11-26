FROM python:3.11.10-slim-bullseye

ENV APP_ROOT=/code
ENV HOME=/root
WORKDIR ${APP_ROOT}

# Install core packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gnupg \
        lsb-release \
        openssh-client \
        rclone \
        rsync \
        s3fs \
        sshpass \
        tzdata \
        wget
# Install database client.
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get -y install \
        postgresql-client-15

# Set the image timezone...
ENV TZ=UTC

# Populate the image...
RUN /usr/local/bin/python -m pip install --upgrade pip && \
    pip install boto3==1.14.32

COPY backup.py ${APP_ROOT}/
COPY docker-entrypoint.sh ${APP_ROOT}/
COPY pgpass ${HOME}/.pgpass
COPY rclone.conf ${HOME}/.config/rclone/rclone.conf
RUN chmod 755 ${APP_ROOT}/*.py && \
    chmod 755 ${APP_ROOT}/*.sh && \
    chmod 755 ${HOME}/.config/rclone/rclone.conf && \
    chmod 600 ${HOME}/.pgpass && \
    mkdir ${HOME}/.ssh && \
    chmod 700 ${HOME}/.ssh

# Force the binary layer of the stdout and stderr streams
# to be unbuffered
ENV PYTHONUNBUFFERED=1

CMD [ "./docker-entrypoint.sh" ]
