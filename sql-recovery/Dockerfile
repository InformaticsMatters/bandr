FROM python:3.10.9-slim-buster

# Create the 'exepcted' Recovery directory.
# The recovery container may somethign mounted here, it may not.
WORKDIR /recovery

ENV APP_ROOT /code
ENV HOME /root
WORKDIR ${APP_ROOT}

# Install core packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gnupg \
        lsb-release \
        openssh-client \
        rsync \
        s3fs \
        sshpass \
        tzdata \
        wget
# Install database clients
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get -y install \
        postgresql-client-15

# Set the image timezone...
ENV TZ=UTC

# Populate the image...
RUN /usr/local/bin/python -m pip install --upgrade pip && \
    pip install \
        boto3==1.14.32 \
        python-dateutil==2.8.1

COPY recovery.py ${APP_ROOT}/
COPY docker-entrypoint.sh ${APP_ROOT}/
COPY pgpass ${HOME}/.pgpass
RUN chmod 755 ${APP_ROOT}/*.py && \
    chmod 755 ${APP_ROOT}/*.sh && \
    chmod 600 ${HOME}/.pgpass && \
    mkdir ${HOME}/.ssh && \
    chmod 700 ${HOME}/.ssh

# Force the binary layer of the stdout and stderr streams
# to be unbuffered
ENV PYTHONUNBUFFERED 1

CMD [ "./docker-entrypoint.sh" ]
