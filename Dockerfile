FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Prevent Python from buffering stdout (so logs show up immediately)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Ensure browsers are installed (though usually present in this image)
RUN playwright install chromium

# Copy the rest of your code
COPY . .

# Expose port for status server
EXPOSE 5000

# Create a simple runner script to handle the "Daily" logic
CMD ["python", "main.py"]