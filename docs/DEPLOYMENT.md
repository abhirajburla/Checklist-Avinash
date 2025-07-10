# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Construction Checklist Matching System to production environments. The system is designed to be flexible and can be deployed on various platforms and configurations.

## 🎯 Deployment Options

### 1. Local Development
- **Purpose**: Development and testing
- **Requirements**: Python 3.8+, local environment
- **Best For**: Individual developers, small teams

### 2. Docker Containerization
- **Purpose**: Isolated, reproducible deployments
- **Requirements**: Docker, Docker Compose
- **Best For**: Development teams, staging environments

### 3. Cloud Deployment
- **Purpose**: Scalable, production-ready deployment
- **Requirements**: Cloud platform (AWS, GCP, Azure)
- **Best For**: Production environments, high availability

### 4. On-Premises Deployment
- **Purpose**: Internal infrastructure deployment
- **Requirements**: Internal servers, network access
- **Best For**: Enterprise environments, data security requirements

## 🚀 Quick Start Deployment

### Prerequisites

1. **Python Environment**
   ```bash
   # Python 3.8 or higher
   python --version
   ```

2. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   ```bash
   # Create .env file
   GEMINI_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

4. **File Permissions**
   ```bash
   # Ensure upload directories exist
   mkdir -p uploads cache results
   chmod 755 uploads cache results
   ```

### Basic Local Deployment

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd Checklist-Avinash
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Copy environment template
   cp dot\ env\ file.txt .env
   
   # Edit .env file with your settings
   nano .env
   ```

4. **Run Application**
   ```bash
   python app.py
   ```

5. **Access Application**
   ```
   http://localhost:5000
   ```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads cache results

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  checklist-app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - BATCH_SIZE=50
      - MAX_RETRIES=3
    volumes:
      - ./uploads:/app/uploads
      - ./cache:/app/cache
      - ./results:/app/results
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - checklist-app
    restart: unless-stopped
```

### Docker Deployment Steps

1. **Build and Run**
   ```bash
   # Build image
   docker build -t checklist-matching .
   
   # Run container
   docker run -d \
     --name checklist-app \
     -p 5000:5000 \
     -e GEMINI_API_KEY=your_key \
     -v $(pwd)/uploads:/app/uploads \
     checklist-matching
   ```

2. **Using Docker Compose**
   ```bash
   # Start services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop services
   docker-compose down
   ```

## ☁️ Cloud Deployment

### AWS Deployment

#### EC2 Deployment

1. **Launch EC2 Instance**
   ```bash
   # Launch Ubuntu 20.04 instance
   # Instance type: t3.medium or larger
   # Storage: 20GB minimum
   ```

2. **Install Dependencies**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install -y python3 python3-pip python3-venv nginx
   
   # Install system dependencies
   sudo apt install -y gcc build-essential
   ```

3. **Deploy Application**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd Checklist-Avinash
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment
   cp dot\ env\ file.txt .env
   nano .env
   ```

4. **Configure Systemd Service**
   ```bash
   # Create service file
   sudo nano /etc/systemd/system/checklist-app.service
   ```

   ```ini
   [Unit]
   Description=Checklist Matching Application
   After=network.target
   
   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/Checklist-Avinash
   Environment=PATH=/home/ubuntu/Checklist-Avinash/venv/bin
   ExecStart=/home/ubuntu/Checklist-Avinash/venv/bin/python app.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

5. **Start Service**
   ```bash
   # Enable and start service
   sudo systemctl enable checklist-app
   sudo systemctl start checklist-app
   
   # Check status
   sudo systemctl status checklist-app
   ```

6. **Configure Nginx**
   ```bash
   # Create nginx configuration
   sudo nano /etc/nginx/sites-available/checklist-app
   ```

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
   
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   
       location /uploads {
           alias /home/ubuntu/Checklist-Avinash/uploads;
       }
   }
   ```

   ```bash
   # Enable site
   sudo ln -s /etc/nginx/sites-available/checklist-app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

#### AWS ECS Deployment

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name checklist-matching
   ```

2. **Build and Push Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and tag image
   docker build -t checklist-matching .
   docker tag checklist-matching:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/checklist-matching:latest
   
   # Push image
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/checklist-matching:latest
   ```

3. **Create ECS Task Definition**
   ```json
   {
     "family": "checklist-matching",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "checklist-app",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/checklist-matching:latest",
         "portMappings": [
           {
             "containerPort": 5000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "GEMINI_API_KEY",
             "value": "your_api_key"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/checklist-matching",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

### Google Cloud Platform Deployment

#### GCP App Engine

1. **Create app.yaml**
   ```yaml
   runtime: python39
   
   env_variables:
     GEMINI_API_KEY: "your_api_key"
     SECRET_KEY: "your_secret_key"
   
   handlers:
   - url: /static
     static_dir: static
   
   - url: /.*
     script: auto
   ```

2. **Deploy to App Engine**
   ```bash
   gcloud app deploy
   ```

#### GCP Cloud Run

1. **Build and Deploy**
   ```bash
   # Build image
   gcloud builds submit --tag gcr.io/PROJECT_ID/checklist-matching
   
   # Deploy to Cloud Run
   gcloud run deploy checklist-matching \
     --image gcr.io/PROJECT_ID/checklist-matching \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY=your_api_key
   ```

### Azure Deployment

#### Azure App Service

1. **Create App Service**
   ```bash
   az group create --name checklist-rg --location eastus
   az appservice plan create --name checklist-plan --resource-group checklist-rg --sku B1
   az webapp create --name checklist-app --resource-group checklist-rg --plan checklist-plan --runtime "PYTHON|3.9"
   ```

2. **Configure Environment Variables**
   ```bash
   az webapp config appsettings set --name checklist-app --resource-group checklist-rg --settings GEMINI_API_KEY=your_api_key
   ```

3. **Deploy Application**
   ```bash
   az webapp deployment source config-local-git --name checklist-app --resource-group checklist-rg
   git remote add azure <git-url>
   git push azure main
   ```

## 🔧 Production Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key

# Optional (with defaults)
GEMINI_MODEL=gemini-2.5-pro
BATCH_SIZE=50
MAX_RETRIES=3
ENABLE_SYSTEM_INSTRUCTIONS=true
ENABLE_REFERENCE_VALIDATION=true
MAX_CONTENT_LENGTH=838860800
UPLOAD_FOLDER=uploads
CACHE_FOLDER=cache
RESULTS_FOLDER=results
LOG_LEVEL=INFO
```

### Security Configuration

1. **HTTPS Setup**
   ```bash
   # Install SSL certificate
   sudo certbot --nginx -d your-domain.com
   ```

2. **Firewall Configuration**
   ```bash
   # Configure UFW
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

3. **File Permissions**
   ```bash
   # Secure file permissions
   chmod 755 uploads cache results
   chmod 600 .env
   ```

### Performance Optimization

1. **Gunicorn Configuration**
   ```bash
   # Install Gunicorn
   pip install gunicorn
   
   # Create gunicorn config
   nano gunicorn.conf.py
   ```

   ```python
   bind = "127.0.0.1:5000"
   workers = 4
   worker_class = "sync"
   worker_connections = 1000
   timeout = 30
   keepalive = 2
   max_requests = 1000
   max_requests_jitter = 100
   ```

2. **Nginx Configuration**
   ```nginx
   upstream checklist_app {
       server 127.0.0.1:5000;
   }
   
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
   
       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
   
       client_max_body_size 800M;
   
       location / {
           proxy_pass http://checklist_app;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 300s;
           proxy_connect_timeout 75s;
       }
   
       location /uploads {
           alias /path/to/uploads;
           expires 1h;
           add_header Cache-Control "public, immutable";
       }
   }
   ```

## 📊 Monitoring and Logging

### Application Logging

1. **Log Configuration**
   ```python
   import logging
   from logging.handlers import RotatingFileHandler
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
       handlers=[
           RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10),
           logging.StreamHandler()
       ]
   )
   ```

2. **Health Check Endpoint**
   ```python
   @app.route('/health')
   def health_check():
       return jsonify({
           'status': 'healthy',
           'timestamp': datetime.utcnow().isoformat(),
           'version': '1.0.0'
       })
   ```

### System Monitoring

1. **Systemd Service Monitoring**
   ```bash
   # Check service status
   sudo systemctl status checklist-app
   
   # View logs
   sudo journalctl -u checklist-app -f
   ```

2. **Resource Monitoring**
   ```bash
   # Monitor system resources
   htop
   df -h
   free -h
   ```

## 🔄 Backup and Recovery

### Data Backup

1. **File Backup Strategy**
   ```bash
   # Create backup script
   nano backup.sh
   ```

   ```bash
   #!/bin/bash
   BACKUP_DIR="/backups/checklist-app"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   # Create backup directory
   mkdir -p $BACKUP_DIR
   
   # Backup uploads
   tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/
   
   # Backup results
   tar -czf $BACKUP_DIR/results_$DATE.tar.gz results/
   
   # Backup configuration
   cp .env $BACKUP_DIR/env_$DATE
   
   # Clean old backups (keep 7 days)
   find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
   ```

2. **Automated Backup**
   ```bash
   # Add to crontab
   crontab -e
   
   # Add line for daily backup at 2 AM
   0 2 * * * /path/to/backup.sh
   ```

### Recovery Procedures

1. **Application Recovery**
   ```bash
   # Stop application
   sudo systemctl stop checklist-app
   
   # Restore from backup
   tar -xzf /backups/checklist-app/uploads_20240115_020000.tar.gz
   tar -xzf /backups/checklist-app/results_20240115_020000.tar.gz
   
   # Restart application
   sudo systemctl start checklist-app
   ```

2. **Database Recovery** (if applicable)
   ```bash
   # Restore database from backup
   # (Implementation depends on database choice)
   ```

## 🧪 Testing Deployment

### Pre-Deployment Testing

1. **Unit Tests**
   ```bash
   python -m pytest tests/ -v
   ```

2. **Integration Tests**
   ```bash
   # Test API endpoints
   curl http://localhost:5000/health
   curl http://localhost:5000/
   ```

3. **Load Testing**
   ```bash
   # Install Apache Bench
   sudo apt install apache2-utils
   
   # Run load test
   ab -n 1000 -c 10 http://localhost:5000/
   ```

### Post-Deployment Verification

1. **Health Check**
   ```bash
   curl -f http://your-domain.com/health
   ```

2. **Functionality Test**
   ```bash
   # Test file upload
   curl -X POST http://your-domain.com/upload \
     -F "drawing_file=@test.pdf"
   ```

3. **Performance Test**
   ```bash
   # Monitor response times
   curl -w "@curl-format.txt" -o /dev/null -s http://your-domain.com/
   ```

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   sudo lsof -i :5000
   
   # Kill process
   sudo kill -9 <PID>
   ```

2. **Permission Denied**
   ```bash
   # Fix file permissions
   sudo chown -R ubuntu:ubuntu /path/to/app
   chmod 755 uploads cache results
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   free -h
   
   # Increase swap if needed
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Log Analysis

1. **Application Logs**
   ```bash
   tail -f logs/app.log
   grep ERROR logs/app.log
   ```

2. **System Logs**
   ```bash
   sudo journalctl -u checklist-app -f
   sudo tail -f /var/log/nginx/error.log
   ```

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancer Setup**
   ```bash
   # Configure multiple instances behind load balancer
   # Use AWS ALB, GCP Load Balancer, or nginx upstream
   ```

2. **Session Management**
   ```bash
   # Use Redis for session storage
   pip install redis flask-session
   ```

### Vertical Scaling

1. **Resource Optimization**
   ```bash
   # Increase worker processes
   # Optimize batch sizes
   # Add more memory/CPU
   ```

2. **Caching Strategy**
   ```bash
   # Implement Redis caching
   # Use CDN for static files
   # Optimize database queries
   ```

---

This deployment guide provides comprehensive instructions for deploying the Construction Checklist Matching System to various environments. Choose the deployment method that best fits your requirements and infrastructure. 