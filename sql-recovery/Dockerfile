FROM python:3.7.0-alpine3.8

ENV APP_ROOT /code
ENV HOME /root
WORKDIR ${APP_ROOT}

# Install stuff including PostgreSQL and MySQL clients
RUN apk add --no-cache postgresql-client \
        mysql-client \
        tzdata rsync openssh && \
    rm -rf /var/cache/apk/*
# Set the Alpine image timezone...
ENV TZ=UTC

# Populate the image...
COPY recovery.py ${APP_ROOT}/
RUN chmod 755 ${APP_ROOT}/recovery.py
COPY pgpass ${HOME}/.pgpass
RUN chmod 600 ${HOME}/.pgpass

# Force the binary layer of the stdout and stderr streams
# to be unbuffered
ENV PYTHONUNBUFFERED 1

CMD [ "./recovery.py" ]
