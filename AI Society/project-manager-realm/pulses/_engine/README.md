# Pulses Engine

This directory contains the runtime engine for executing `pulse.yaml` workflows for the project-manager-realm.

Responsibilities:
- Execute steps sequentially or in parallel as defined by the pulse
- Support retry policies, backoff, and compensation handlers
- Instrumentation for metrics and tracing

Next: implement a lightweight executor in your preferred language (Node/NestJS, Python, or Go).