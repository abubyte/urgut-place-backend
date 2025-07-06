# Urgut Please - Shop Finding Platform Backend

## Video Demo: [URL to your video demo]

## Description
Urgut Please is a robust RESTful API backend that powers a shop finding and rating platform. The backend provides a comprehensive set of endpoints for user authentication, shop management, ratings, and reviews. It's designed to be scalable, secure, and maintainable, serving as the foundation for any frontend application that needs to interact with shop rating data.

### Key Features
- **RESTful API**: Well-documented endpoints following REST principles
- **User Authentication**: Secure JWT-based authentication system
- **Shop Management**: CRUD operations for shop listings
- **Rating System**: Comprehensive rating and review functionality
- **Like System**: API endpoints for review interactions
- **Category Management**: Organized shop categorization
- **Search and Filter**: Advanced querying capabilities

## API Endpoints

### Authentication & Users (`/users`)
- `POST /users/register` - Register a new user
- `POST /users/verify` - Verify user's phone/email
- `POST /users/login` - Login and get access token
- `POST /users/refresh` - Refresh access token
- `GET /users/me` - Get current user info
- `GET /users/{user_id}` - Get user by ID
- `GET /users` - List all users (admin only)
- `DELETE /users/{user_id}` - Delete user (self or admin)

### Shops (`/shops`)
- `GET /shops` - List shops with filtering, search, and pagination
- `GET /shops/{shop_id}` - Get shop details
- `POST /shops` - Create new shop
- `PATCH /shops/{shop_id}` - Update shop
- `DELETE /shops/{shop_id}` - Delete shop
- `PATCH /shops/{shop_id}/feature` - Toggle featured status (admin only)

### Categories (`/categories`)
- `GET /categories` - List all categories
- `GET /categories/{category_id}` - Get category details
- `POST /categories` - Create category (admin only)
- `PUT /categories/{category_id}` - Update category (admin only)
- `DELETE /categories/{category_id}` - Delete category (admin only)

### Ratings (`/ratings`)
- `POST /ratings` - Create a new rating
- `GET /ratings/{rating_id}` - Get rating details
- `GET /ratings/shop/{shop_id}` - Get all ratings for a shop
- `PATCH /ratings/{rating_id}` - Update rating
- `DELETE /ratings/{rating_id}` - Delete rating

### Likes (`/likes`)
- `POST /likes` - Like a shop (clients only)
- `GET /likes` - List user's likes
- `DELETE /likes/{like_id}` - Remove a like

## Design Choices
- **Backend Framework**: FastAPI was chosen for its modern approach, automatic API documentation, and high performance
- **Database**: PostgreSQL for robust data management and complex relationships
- **Authentication**: JWT tokens with bcrypt password hashing for secure user management
- **Architecture**: Clean architecture pattern with separate modules for better maintainability
- **Testing**: Comprehensive test suite using pytest for reliability

## Technical Implementation
The project is built using:
- Python 3
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT for authentication
- Alembic for database migrations

### Project Structure
```
backend/
├── alembic/          # Database migrations
├── app/
│   ├── api/         # API endpoints
│   ├── auth/        # Authentication logic
│   ├── core/        # Core configurations
│   ├── crud/        # Database operations
│   ├── models/      # Database models
│   ├── schemas/     # Pydantic schemas
│   ├── users/       # User management
│   ├── shops/       # Shop management
│   ├── ratings/     # Rating system
│   ├── categories/  # Category management
│   └── likes/       # Like system
├── tests/           # Test suite
└── requirements.txt # Project dependencies
```

## How to Run
1. Clone the repository
```bash
git clone [repository-url]
cd urgut_please/backend
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/urgut_please
SECRET_KEY=your-secret-key
```

5. Run database migrations
```bash
alembic upgrade head
```

6. Start the application
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation
Once the application is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`


## Future Improvements
- Real-time notifications using WebSockets
- Advanced search with Elasticsearch integration
- Analytics endpoints for shop owners
- Enhanced security features
