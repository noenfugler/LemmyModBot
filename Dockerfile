FROM pytorch/pytorch

RUN apt update \
    && apt install -yqq wget git gnupg curl python3-pip nvidia-cuda-toolkit nvidia-cuda-toolkit-gcc
RUN pip3 install pipenv

# Copy source files
COPY . /app
WORKDIR /app
RUN pipenv install --system --deploy --ignore-pipfile

CMD ["python", "-m", "/app/main.py"]