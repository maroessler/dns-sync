FROM python:3.13
# Or any preferred Python version.
ADD adguardhome.py dns-sync.py requirements.yaml .
RUN pip install -r requirements.yaml
CMD ["python", "-u", "./dns-sync.py"] 
