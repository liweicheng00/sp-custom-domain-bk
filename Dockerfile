FROM python:3.8

# RUN curl -fsSL https://get.pulumi.com | sh
# ENV PATH="/root/.pulumi/bin:${PATH}"

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

ARG S3_BUCKET_DOMAIN_NAME
ARG DEFAULT_PROJECT_DOMAIN_NAME
ARG HOSTED_ZONE_ID
ENV AWS_ACCESS_KEY_ID = ${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY = ${AWS_SECRET_ACCESS_KEY}

ENV S3_BUCKET_DOMAIN_NAME = ${S3_BUCKET_DOMAIN_NAME}
ENV DEFAULT_PROJECT_DOMAIN_NAME = ${DEFAULT_PROJECT_DOMAIN_NAME}
ENV HOSTED_ZONE_ID = ${HOSTED_ZONE_ID}

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app

EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
