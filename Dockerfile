FROM ubuntu:22.04

# Install dependencies (including libaio-dev for Oracle Client)
RUN apt-get update && apt-get install -y \
    libaio1 \
    libaio-dev \
    wget \
    unzip \
    python3 \
    python3-pip \
    ca-certificates \
    libc6 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Oracle Instant Client
WORKDIR /opt/oracle
RUN wget --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" \
    https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linuxx64.zip && \
    unzip instantclient-basic-linuxx64.zip && \
    rm instantclient-basic-linuxx64.zip

# Rename the extracted directory to a consistent name
RUN EXTRACTED_DIR=$(ls -d instantclient* 2>/dev/null | head -1) && \
    if [ -n "$EXTRACTED_DIR" ] && [ "$EXTRACTED_DIR" != "instantclient" ]; then \
        mv "$EXTRACTED_DIR" instantclient; \
        echo "Renamed $EXTRACTED_DIR to instantclient"; \
    fi

WORKDIR /opt/oracle/instantclient

# Create symlink for libclntsh.so if it doesn't exist
RUN if [ ! -f "libclntsh.so" ]; then \
        VERSIONED_LIB=$(ls libclntsh.so.* 2>/dev/null | head -1) && \
        if [ -n "$VERSIONED_LIB" ]; then \
            ln -s "$VERSIONED_LIB" libclntsh.so; \
            echo "Created symlink: libclntsh.so -> $VERSIONED_LIB"; \
        fi; \
    fi

# Verify the library exists and check dependencies
RUN echo "=== Oracle Instant Client libraries ===" && \
    ls -la libclntsh.so* 2>/dev/null && \
    echo "\n=== Checking library dependencies ===" && \
    ldd libclntsh.so 2>&1 | head -20 || echo "ldd check completed"

# Make all files readable and executable
RUN chmod -R 755 /opt/oracle/instantclient

# Set environment variables
# Note: We set LD_LIBRARY_PATH but it may not be available at build time
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV PATH=/opt/oracle/instantclient:$PATH

# Run ldconfig to update the library cache
RUN echo "/opt/oracle/instantclient" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Verify ldconfig registered the library
RUN ldconfig -p | grep libclntsh || echo "Warning: libclntsh not found in ldconfig cache"

WORKDIR /app

# Copy dependency files first (for better Docker layer caching)
COPY requirements.txt ./

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py ./
COPY src/ ./src/

# Set the entrypoint to run the application
CMD ["python3", "main.py"]