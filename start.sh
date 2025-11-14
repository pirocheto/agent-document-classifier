export OTEL_SERVICE_NAME=agent-classification-fastapi
export OTEL_TRACES_EXPORTER=console
export OTEL_METRICS_EXPORTER=console
export OTEL_LOGS_EXPORTER=none
export TRACELOOP_TRACE_CONTENT=false
export AWS_REGION=eu-west-1
opentelemetry-instrument fastapi run app/main.py 