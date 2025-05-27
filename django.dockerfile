FROM python:3.11-alpine
WORKDIR /home/app
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
WORKDIR /web/admin_app
CMD [ "python", "manage.py", "migrate", "&&", "python", "manage.py", "runserver"]