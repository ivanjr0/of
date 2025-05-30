# Content Management System - React Frontend

This is the React-based frontend for the Content Management System, migrated from a vanilla HTML/JavaScript implementation to a modern React application.

## Migration Overview

The frontend has been completely migrated from:
- **Before**: Vanilla HTML, CSS, and JavaScript with Express.js server
- **After**: React 18 application with modern component architecture

### Key Improvements

1. **Modern React Architecture**: Component-based structure with hooks and functional components
2. **Better State Management**: Centralized state management with React hooks
3. **Improved Developer Experience**: Hot reloading, TypeScript support, and modern tooling
4. **Enhanced Performance**: Optimized builds with code splitting and tree shaking
5. **Better Maintainability**: Modular component structure and utility functions

## Features

- **Upload Content**: Drag-and-drop file upload with validation
- **Content Library**: Browse, search, and filter uploaded content
- **AI Analysis Display**: View AI-powered content analysis results
- **Responsive Design**: Mobile-friendly interface
- **Real-time Updates**: Live status updates for content processing
- **Modal Views**: Detailed content viewing with metadata
- **Toast Notifications**: User-friendly feedback system

## Technology Stack

- **React 18**: Modern React with hooks and functional components
- **Axios**: HTTP client for API communication
- **React Hot Toast**: Toast notification system
- **Lucide React**: Modern icon library
- **CSS3**: Custom styling with modern CSS features
- **Font Awesome**: Icon library for UI elements

## Project Structure

```
src/
├── components/          # React components
│   ├── Header.js       # Application header
│   ├── TabNavigation.js # Tab switching component
│   ├── UploadTab.js    # File upload interface
│   ├── LibraryTab.js   # Content library view
│   ├── ContentItem.js  # Individual content card
│   ├── ContentModal.js # Content detail modal
│   ├── EmptyState.js   # Empty/error state component
│   └── LoadingSpinner.js # Loading indicator
├── utils/              # Utility functions
│   ├── api.js         # API communication
│   └── helpers.js     # Helper functions
├── App.js             # Main application component
├── App.css            # Application styles
├── index.js           # Application entry point
└── index.css          # Global styles
```

## Development

### Prerequisites

- Node.js 18 or higher
- npm or yarn package manager

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Development Server

The development server runs on `http://localhost:3000` and includes:
- Hot reloading for instant updates
- Error overlay for debugging
- Proxy configuration for API requests

### API Integration

The frontend communicates with the backend API through:
- **Base URL**: `/api` (proxied to backend in development)
- **Endpoints**:
  - `POST /api/content` - Upload new content
  - `GET /api/content` - Fetch all content
  - `GET /api/content/:id` - Fetch specific content
  - `DELETE /api/content/:id` - Delete content
  - `GET /api/health` - Health check

## Docker Deployment

### Multi-stage Build

The Dockerfile uses a multi-stage build process:

1. **Build Stage**: Compiles React application
2. **Production Stage**: Serves static files with `serve`

### Build and Run

```bash
# Build Docker image
docker-compose build frontend

# Run with docker-compose
docker-compose up frontend

# Run standalone
docker run -p 3000:3000 of-frontend
```

### Health Checks

The container includes health checks that verify:
- Application is responding on port 3000
- Static files are being served correctly

## Environment Variables

- `NODE_ENV`: Environment mode (development/production)
- `PORT`: Server port (default: 3000)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance Optimizations

- **Code Splitting**: Automatic code splitting with React.lazy
- **Tree Shaking**: Unused code elimination
- **Asset Optimization**: Minified CSS and JavaScript
- **Gzip Compression**: Compressed static assets
- **Caching**: Optimized caching headers

## Migration Notes

### Removed Files
- `server.js` - Express server (replaced with static serving)
- `index.html` - Static HTML (replaced with React-generated HTML)
- `script.js` - Vanilla JavaScript (replaced with React components)
- `styles.css` - Global styles (reorganized into component styles)

### Preserved Functionality
- All original features maintained
- Same API endpoints and data flow
- Identical user interface and experience
- Same Docker deployment process

### New Features
- Component-based architecture
- Better error handling
- Improved accessibility
- Enhanced mobile responsiveness
- Modern development tooling

## Troubleshooting

### Common Issues

1. **Build Failures**: Ensure Node.js 18+ is installed
2. **API Connection**: Check backend server is running
3. **Port Conflicts**: Ensure port 3000 is available
4. **Docker Issues**: Verify Docker daemon is running

### Debug Mode

Enable debug logging by setting:
```bash
export DEBUG=true
npm start
```

## Contributing

1. Follow React best practices
2. Use functional components with hooks
3. Maintain consistent code style
4. Add proper error handling
5. Include appropriate tests

## License

MIT License - see LICENSE file for details. 