#!/bin/bash
# Setup local development environment for Speech Memorization Platform

set -e

echo "🏠 Setting up local development environment..."

# Check if we're in the project root
if [ ! -f "manage.py" ]; then
    echo "❌ Please run this script from the project root directory (where manage.py is located)"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    
    # Generate a secure Django SECRET_KEY
    echo "🔑 Generating secure Django SECRET_KEY..."
    SECRET_KEY=$(python3 -c "
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
")
    
    # Update the .env file with the generated key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=django-insecure-local-development-key-change-this-to-secure-random-string/SECRET_KEY=$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=django-insecure-local-development-key-change-this-to-secure-random-string/SECRET_KEY=$SECRET_KEY/" .env
    fi
    
    echo "✅ Created .env file with secure SECRET_KEY"
    echo "📝 Please edit .env and update the following values:"
    echo "   - OPENAI_API_KEY (if you plan to use AI features)"
    echo "   - DATABASE_URL (if you want to use PostgreSQL instead of SQLite)"
    echo "   - GOOGLE_CLOUD_PROJECT_ID (your actual project ID)"
else
    echo "✅ .env file already exists"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗃️  Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (optional)
echo ""
read -p "🤔 Would you like to create a Django superuser? (y/N): " create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "🎉 Local development environment setup complete!"
echo ""
echo "🚀 To start the development server:"
echo "   python manage.py runserver"
echo ""
echo "🌐 Your app will be available at:"
echo "   http://localhost:8000"
echo ""
echo "🔧 Admin interface (if you created a superuser):"
echo "   http://localhost:8000/admin"
echo ""
echo "📋 Environment configuration:"
echo "   - Settings: speech_memorization.settings_cloud"
echo "   - Database: SQLite (db.sqlite3)"
echo "   - Secrets: .env file"
echo ""
echo "💡 Tips:"
echo "   - Edit .env to customize your local configuration"
echo "   - Use 'python manage.py shell' for Django shell access"
echo "   - Use 'python manage.py dbshell' for database shell access"