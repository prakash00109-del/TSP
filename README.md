# PG Management System

A comprehensive PG (Paying Guest) management system built with Flask and PostgreSQL for managing tenants, rooms, and beds.

## Features

- 🏠 Floor, Room, and Bed Management
- 👥 Tenant Registration and Management
- 📊 Export Data to CSV and PDF
- 📸 Photo and Document Upload
- 🚫 Former Tenants Tracking
- 📱 Responsive Web Interface

## Deployment on Vercel

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **PostgreSQL Database**: Set up a PostgreSQL database (recommended: Supabase, Railway, or Neon)
3. **GitHub Repository**: Push your code to GitHub

### Setup Steps

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Set Environment Variables**:
   - Get your database URL from your PostgreSQL provider
   - Set `DATABASE_URL` in Vercel dashboard under Settings > Environment Variables

4. **Deploy**:
   ```bash
   vercel --prod
   ```

### Environment Variables

Required environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `FLASK_ENV`: Set to `production`
- `SECRET_KEY`: Flask secret key

Example:
```
DATABASE_URL=postgresql://username:password@hostname:port/database_name
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
```

### Database Setup

1. Create a PostgreSQL database
2. The application will automatically create the required tables
3. Tables created: `rooms`, `former_tenants`

### File Structure

```
├── api/
│   └── index.py          # Vercel serverless function entry point
├── static/
│   ├── style.css         # Application styles
│   └── fontawesome.min.css # Font Awesome icons
├── templates/
│   └── index.html        # Main application template
├── app.py                # Flask application
├── database.py           # Database operations
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
├── package.json         # Node.js dependencies for Vercel
└── .env.example         # Environment variables template
```

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database URL
   ```

3. **Run locally**:
   ```bash
   python app.py
   ```

### Deployment Commands

- **Deploy to production**: `vercel --prod`
- **Deploy preview**: `vercel`
- **View logs**: `vercel logs`

## Database Providers

Recommended PostgreSQL providers for Vercel deployment:

1. **Supabase** - Free tier available
2. **Neon** - Serverless PostgreSQL
3. **Railway** - Easy PostgreSQL setup
4. **Heroku** - Postgres as a service

## Support

For issues with deployment:
- Check Vercel logs: `vercel logs`
- Verify environment variables in Vercel dashboard
- Ensure database is accessible from Vercel

## License

ISC
