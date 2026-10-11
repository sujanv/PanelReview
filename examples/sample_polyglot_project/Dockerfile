# Multi-stage Dockerfile for Polyglot Service
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server main.go

FROM alpine:3.19
RUN apk --no-cache add ca-certificates
RUN adduser -D -u 10001 appuser

WORKDIR /app
COPY --from=builder /app/server /app/server
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:8080/healthz || exit 1

ENTRYPOINT ["/app/server"]
