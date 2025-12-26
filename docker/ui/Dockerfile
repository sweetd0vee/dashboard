FROM python:3.12-slim

RUN mkdir /work

WORKDIR /work

COPY ./src/ui/requirements.txt /work
RUN pip install --no-cache-dir --timeout 1000 --retries 5 -r requirements.txt


RUN mkdir /work/ui
RUN mkdir /work/ui/assets
RUN mkdir /work/ui/components
RUN mkdir /work/ui/pages
RUN mkdir /work/ui/utils


COPY ./src/ui/*.py /work/ui
COPY ./src/ui/assets/*.* /work/ui/assets
COPY ./src/ui/components/*.py /work/ui/components
COPY ./src/ui/pages/*.py /work/ui/pages
COPY ./src/ui/utils/*.py /work/ui/utils

COPY ./base_logger.py /work

WORKDIR /work/ui

CMD ["streamlit", "run", "main.py"]
