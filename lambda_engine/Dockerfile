FROM public.ecr.aws/lambda/python:3.12

# Install dependencies
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    yfinance

# Copy source code
COPY main.py ${LAMBDA_TASK_ROOT}

# Set the handler
CMD [ "main.handler" ]
