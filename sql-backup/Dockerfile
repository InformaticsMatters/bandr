FROM python:3.9.0-alpine3.12

ENV APP_ROOT /code
ENV HOME /root
WORKDIR ${APP_ROOT}

# Install stuff including PostgreSQL and MySQL clients
RUN apk add --no-cache \
        mysql-client=10.4.15-r0 \
        openssh \
        postgresql-client=12.4-r0 \
        rsync \
        sshpass \
        tzdata && \
    rm -rf /var/cache/apk/*
# Set the Alpine image timezone...
ENV TZ=UTC

# Populate the image...
COPY backup.py ${APP_ROOT}/
COPY pgpass ${HOME}/.pgpass
RUN /usr/local/bin/python -m pip install --upgrade pip && \
    pip install boto3==1.14.32 && \
    chmod 755 ${APP_ROOT}/backup.py && \
    chmod 600 ${HOME}/.pgpass && \
    mkdir ${HOME}/.ssh && \
    chmod 700 ${HOME}/.ssh

# Force the binary layer of the stdout and stderr streams
# to be unbuffered
ENV PYTHONUNBUFFERED 1

CMD [ "./backup.py" ]
