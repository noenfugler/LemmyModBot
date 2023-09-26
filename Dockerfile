FROM pytorch/pytorch

RUN pip3 install pipenv

# Copy source files
COPY . /app
WORKDIR /app
RUN pipenv install --system --deploy --ignore-pipfile

CMD ["python", "-m", "/app/main.py"]