FROM python:3.8.7
EXPOSE 8000

RUN pip install -q pipenv
WORKDIR project
COPY . .
RUN pipenv install --system --deploy

WORKDIR /project
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0"]
