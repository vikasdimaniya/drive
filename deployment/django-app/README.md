# Django Application Deployment

This directory contains the necessary files to deploy the Django application using Docker.

## Files

- `Dockerfile`: Defines how to build the Django application container
- `docker-compose.yml`: Defines the services needed to run the application
- `.env.example`: Example environment variables file

## Deployment Instructions

1. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual values:
   ```
   DJANGO_SECRET_KEY=your-secure-secret-key
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   PORT=3011  # Change this if you want to use a different port
   ```

3. Build and start the application:
   ```bash
   docker-compose up -d
   ```

4. The application will be available at http://localhost:3011 (or whatever port you specified)

## Changing the Port

You can change the port in several ways:

1. **Using environment variables when running docker-compose**:
   ```bash
   PORT=5000 docker-compose up -d
   ```

2. **Modifying your .env file**:
   ```
   PORT=5000
   ```

3. **Directly in the docker-compose command**:
   ```bash
   docker-compose up -d -e PORT=5000
   ```

## Database Connection

This deployment assumes you have an external PostgreSQL database. Make sure:
1. Your database is accessible from the Docker container
2. The database credentials in your `.env` file are correct
3. The database has the necessary permissions for the Django application 