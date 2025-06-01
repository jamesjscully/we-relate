FROM arizephoenix/phoenix:latest

# Set environment variables for Cloud Run
ENV PORT=8080
ENV PHOENIX_WORKING_DIR=/app/data
ENV PHOENIX_HOST=0.0.0.0

# Expose the port that Cloud Run expects
EXPOSE $PORT

# Start Phoenix server on Cloud Run port (override default 6006)
CMD ["python", "-m", "phoenix.server.main", "--host", "0.0.0.0", "--port", "8080"] 