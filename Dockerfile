FROM python:3.9-slim-buster
LABEL org.opencontainers.image.source="https://github.com/SkyhighSecurity/uploadscanner"
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
