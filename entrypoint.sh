#!/bin/sh -

set -o errexit
set -o nounset

case $1 in
    dev)
        nohup python manage.py migrate --noinput &
        nohup python manage.py collectstatic --noinput &
        exec python manage.py runserver 0.0.0.0:8000;;
    migrate)
        exec python manage.py migrate --noinput;;
    *)
        echo "error: $1 is not a valid entrypoint script argument.  Exiting..."
        exit 1;;
esac
