# Egyptian National ID Validator API

REST API for validating Egyptian National IDs and extracting relevant data, built with Django REST Framework.


## 🚀 Features

### Core Functionality
- **Egyptian National ID Validation**: validation including format and date verification
- **Data Extraction**: Extract birth date, age, gender, governorate, and other information
- **Bulk Validation**: Validate multiple IDs in a single request (up to 100)
- **Caching**: Redis-based caching for improved performance

### Security & Authentication
- **API Key Authentication**: Secure service-to-service authentication
- **Rate Limiting**: Configurable rate limits per API key (per minute/hour/day)
- **IP Restrictions**: Optional IP-based access control

### Monitoring & Analytics
- **Usage Tracking**: Comprehensive API call logging for analytics and billing (can be like daily usage tracking in the future)
- **Error Logging**: Detailed error tracking with categorization
- **Health Monitoring**: Health check endpoints for service monitoring
- **Performance Metrics**: Response time tracking and optimization


## 📋 Requirements

- Python 3.10+
- Docker & Docker Compose (recommended)
- PostgreSQL (for production)
- Redis (for caching and rate limiting)

## 🛠 Installation & Setup

### Option 1: Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd national-id-validator
   ```

2. **Environment Configuration:**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start the services:**
   ```bash
   # Production setup
   docker-compose up -d

   # Development setup
   docker-compose --profile development up -d
   ```

4. **Create default API key:**
   ```bash
   docker-compose exec web python manage.py create_default_api_key
   ```

The API will be available at:
- **Production**: http://localhost (via Nginx)
- **Development**: http://localhost:8001
- **Direct Django**: http://localhost:8000

### Option 2: Local Development

1. **Setup virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment setup:**
   ```bash
   cp .env.example .env
   # Configure your .env file
   ```

4. **Database setup:**
   ```bash
   python manage.py migrate
   python manage.py create_default_api_key
   python manage.py createsuperuser
   ```

5. **Start development server:**
   ```bash
   python manage.py runserver
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Enable debug mode |
| `SECRET_KEY` | `django-insecure-...` | Django secret key |
| `DATABASE_URL` | SQLite | PostgreSQL connection string |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis connection string |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `RATE_LIMIT_PER_MINUTE` | `100` | Default rate limit per minute |
| `API_KEY_HEADER` | `X-API-Key` | API key header name |
| `DEFAULT_API_KEY` | `test-api-key-12345` | Default API key for development |

### Rate Limiting Configuration

Rate limits can be configured per API key in the admin interface:
- **Per minute**: Real-time rate limiting
- **Per hour**: Medium-term usage control
- **Per day**: Long-term usage control

## 📖 API Documentation

### Authentication

All API endpoints require an API key in the request header:

```bash
X-API-Key: your-api-key-here
```

### Endpoints

#### 1. Validate Single National ID

**POST** `/api/v1/validate/`

**Request:**
```json
{
    "national_id": "29001011234567",
    "include_details": true
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "national_id": "29001011234567",
        "is_valid": true,
        "birth_date": "1990-01-01",
        "age": 34,
        "gender": "Male",
        "governorate": "Cairo",
        "governorate_code": "01",
        "century": "20th",
        "sequence_number": "1234",
        "validation_details": {
            "format_valid": true,
            "date_valid": true,
            "governorate_valid": true
        }
    },
    "error": null,
    "timestamp": "2025-07-16T10:30:00Z",
    "processing_time_ms": 5.23
}
```

#### 2. Bulk Validation

**POST** `/api/v1/validate/bulk/`

**Request:**
```json
{
    "national_ids": ["29001011234567", "30012251234568"],
    "include_details": false
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "total_processed": 2,
        "results": [
            {
                "national_id": "29001011234567",
                "is_valid": true,
                "birth_date": "1990-01-01",
                "age": 34,
                "gender": "Male"
            },
            {
                "national_id": "30012251234568",
                "is_valid": true,
                "birth_date": "2001-12-25",
                "age": 23,
                "gender": "Female"
            }
        ]
    },
    "error": null,
    "timestamp": "2025-07-16T10:30:00Z",
    "processing_time_ms": 12.45
}
```

#### 3. Health Check

**GET** `/api/v1/health/`

**Response:**
```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "version": "1.0.0",
        "database": "healthy",
        "cache": "healthy"
    },
    "error": null,
    "timestamp": "2025-07-16T10:30:00Z",
    "processing_time_ms": 1.23
}
```

#### 4. API Documentation

**GET** `/api/v1/docs/`

Returns comprehensive API documentation.

### Rate Limits

- **Single Validation**: 100 requests/minute per IP
- **Bulk Validation**: 50 requests/minute per IP
- **Custom Limits**: Configurable per API key

### Error Responses

All errors follow a consistent format:

```json
{
    "success": false,
    "data": null,
    "error": {
        "code": 400,
        "message": "Detailed error message",
        "type": "ValidationError",
        "field_errors": {
            "national_id": ["This field is required."]
        }
    },
    "timestamp": "2025-07-16T10:30:00Z"
}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Coverage

The project includes comprehensive tests for:
- Core validation logic
- API endpoints
- Authentication & authorization
- Rate limiting
- Error handling
- Usage tracking
- Edge cases and security

### Example Test Commands

```bash
# Test valid Egyptian National IDs
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"national_id": "29001011234567"}' \
     http://localhost:8000/api/v1/validate/

# Test bulk validation
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"national_ids": ["29001011234567", "30012251234568"]}' \
     http://localhost:8000/api/v1/validate/bulk/

# Test health endpoint (no API key required)
curl http://localhost:8000/api/v1/health/
```

## Architecture & Design Decisions

### Core Validation Algorithm

The Egyptian National ID validation implements the official algorithm:

1. **Format Validation**: 14 digits, correct century prefix
2. **Date Validation**: Valid birth date, not in future
3. **Data Extraction**: Birth date, gender, governorate mapping

### Technical Stack

- **Django REST Framework**: Robust API framework
- **PostgreSQL**: Production database with proper indexing
- **Redis**: Caching and rate limiting backend
- **Celery**: Background task processing
- **Nginx**: Reverse proxy and load balancing
- **Docker**: Containerization and orchestration



## 🔒 Security Features

- **API Key Management**: Secure key generation and rotation
- **Rate Limiting**: Multiple levels of protection
- **IP Restrictions**: Optional IP-based access control
- **Input Validation**: Comprehensive sanitization
- **Error Handling**: Secure error messages
- **Audit Logging**: Complete request/response logging

## 📊 Usage Tracking & Analytics

The system tracks:
- API call volumes and patterns
- Response times and performance
- Cache hit rates
- Billable usage units

Access the admin interface at `/admin/` to view detailed analytics.
