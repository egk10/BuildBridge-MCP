#!/bin/bash
# Health endpoint load test
ab -n 1000 -c 10 -g health_plot.tsv "https://localhost/health"
