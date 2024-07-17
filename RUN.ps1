wt redis-server;
wt celery -A MITR_v2 worker --pool=solo -l info;
wt celery -A MITR_v2 beat --loglevel=info;
wt py manage.py runserver;
