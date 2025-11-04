# Frontend - Dashboard UI

React-based frontend for the Lipetsk region governance effectiveness dashboard.

## Features

- Interactive map visualization with choropleth shading
- Rating tables with sorting and pagination
- Analytics dashboard with indicators
- Real-time data updates
- Responsive design (desktop, tablet)
- Tailwind CSS styling

## Project Structure

```
frontend/
├── public/
│   └── index.html           # HTML entry point
├── src/
│   ├── index.jsx            # React entry point
│   ├── App.jsx              # Main app component
│   ├── index.css            # Global styles
│   ├── components/          # Reusable components
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx
│   │   └── ...
│   ├── pages/               # Page components
│   │   ├── MapPage.jsx
│   │   ├── RatingPage.jsx
│   │   └── AnalyticsPage.jsx
│   └── services/            # API services
│       └── api.js           # API client
├── package.json
├── Dockerfile
└── README.md
```

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```
   App will be available at `http://localhost:3000`

3. **Build for production:**
   ```bash
   npm run build
   ```

## Environment Variables

Create `.env` file (optional):
```
REACT_APP_API_URL=http://localhost:8000/api
```

## API Integration

The frontend communicates with the backend API:
- Base URL: `http://localhost:8000/api`
- All requests use Axios with JSON content-type
- See `src/services/api.js` for endpoints

## Components

### Pages
- **MapPage**: Choropleth map with zone shading
- **RatingPage**: Sortable rating table with pagination
- **AnalyticsPage**: Indicators and metrics dashboard

### Components
- **Header**: Top navigation with period selector
- **Sidebar**: Side menu with navigation
- More components can be added to `src/components/`

## Styling

Uses Tailwind CSS with custom configuration for:
- Zone colors (green: #2ecc71, yellow: #f39c12, red: #e74c3c)
- Responsive grid layouts
- Dark sidebar theme

## Development

### Testing
```bash
npm test
```

### Linting
```bash
npm run lint
```

## Docker

Build and run with Docker:
```bash
docker build -t dashboard-frontend .
docker run -p 3000:3000 dashboard-frontend
```

## Performance

- TTFB target: ≤1.5s (with API)
- Pagination: 50 items per page
- Responsive images and icons

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Future Enhancements

- [ ] PDF export for reports
- [ ] Excel export
- [ ] Real-time map tiles (mbtiles)
- [ ] Advanced filtering
- [ ] User authentication (OIDC)
- [ ] Dark mode support
