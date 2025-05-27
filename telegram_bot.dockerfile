FROM python:3.11-alpine
WORKDIR /home/app
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD [ "python", "-m", "tgbot" ]