# Healthcare Assistant Frontend

A production-ready, mobile-first React web app for the Healthcare Planning Assistant.

## Features

- **Mobile-First Design**: Responsive UI optimized for small screens first
- **Fast & Smooth**: Skeleton loaders, smooth animations, and optimized queries

- **Real-Time Feedback**: Loading states, error handling, and retry capabilities
- **Caching**: React Query with intelligent cache management
- **Accessible**: Semantic HTML, ARIA labels, keyboard navigation

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Query (TanStack)** - Data fetching & caching
- **Axios** - HTTP client
- **Lucide React** - Icons

## Project Structure

```
src/
  components/
    InputForm.jsx       - Disease/symptom & location input
    SummaryCard.jsx     - Condition overview section
    HospitalCard.jsx    - Hospital information card
    DoctorCard.jsx      - Doctor/clinic information card
    PlanSection.jsx     - Final healthcare plan display
    Loader.jsx          - Skeleton loaders
  pages/
    Home.jsx           - Main home page
  services/
    api.js             - API client using Axios
  App.jsx              - Root app component
  main.jsx             - React DOM entry point
  index.css            - Tailwind & global styles
```

## Setup

### Prerequisites

- Node.js 16+ and npm/yarn

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (optional, defaults to localhost:8000)
cp .env.example .env

# Start development server
npm run dev
```

The app will open at `http://localhost:5173` by default.

## API Integration

The app expects a backend API at `http://localhost:8000` with endpoint:

```
POST /generate-plan
Request: { topic: string, location: string }
Response: { summary, hospitals, doctors, plan }
```

Set `VITE_API_URL` in `.env` to change the API endpoint.

## Design Philosophy

- **Minimal Typing**: Pre-filled examples, smart validation
- **Thumb-Friendly**: Large buttons, proper spacing on mobile
- **Clean & Calm**: Healthcare-focused color scheme (blue & teal)
- **Fast Feedback**: Loading states, smooth animations, instant validation
- **Readable**: Proper line spacing, clear hierarchy, icons for quick recognition

## Key UX Features

1. **Smart Input Validation**: Real-time error feedback with symbols
2. **Skeleton Loaders**: Shows placeholders while loading (no blank screen)
3. **Smooth Animations**: Fade-in effects for loaded content
4. **Auto-Scroll**: Results automatically scroll into view
5. **Error Recovery**: One-click retry on failures
6. **Theme Persistence**: Dark/light mode preference saved

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Code splitting with lazy loading
- React Query caching to prevent unnecessary API calls
- Optimized re-render with memo components
- Minified production build

## Build for Production

```bash
npm run build
npm run preview
```

Output will be in `dist/` directory.

## Development

- Auto-reload on file changes
- Fast refresh with Vite
- Tailwind CSS JIT compilation
- No-config setup with sensible defaults

## Troubleshooting

**Port 5173 already in use:**
```bash
npm run dev -- --port 3000
```

**Backend not responding:**
- Ensure backend is running on configured URL
- Check `.env` for correct `VITE_API_URL`
- Check browser console for detailed error messages

**Styling not applied:**
- Ensure Tailwind CSS is properly installed
- Check if `src/index.css` is imported in `src/main.jsx`
- Rebuild with `npm run dev`

## License

MIT
