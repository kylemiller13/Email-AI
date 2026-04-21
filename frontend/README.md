# Email Risk AI - React + Chakra UI Frontend

A modern, accessible web application for detecting phishing and malicious emails using AI.

## Features

- 🎨 **Chakra UI** - Beautiful, accessible component library
- 🌙 **Dark Mode** - Enabled by default with Inter font
- 🔵 **Blue Theme** - Professional blue primary color (#3b82f6)
- ⚠️ **Semantic Colors** - Risk colors (Red: critical, Orange: warning, Green: safe)
- 📱 **Responsive** - Mobile-first design
- 🔐 **Google OAuth** - Secure authentication
- ⚡ **Vite** - Lightning-fast development and build

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will open at `http://localhost:3000`

### Build

```bash
npm run build
```

This creates an optimized production build in the `dist/` folder.

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable React components
│   │   ├── EmailCard.tsx       # Email card component
│   │   └── EmailDetailModal.tsx # Email detail modal
│   ├── pages/             # Page components
│   │   ├── Dashboard.tsx   # Main dashboard
│   │   └── SignIn.tsx      # Google OAuth sign-in
│   ├── App.tsx            # Main app component
│   ├── main.tsx           # Entry point
│   ├── theme.ts           # Chakra UI theme configuration
│   └── index.css          # Global styles
├── index.html             # HTML template
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies
```

## Theme Configuration

The theme is configured in `src/theme.ts`:

- **Primary Color**: Brand blue (`#3b82f6`)
- **Semantic Colors**:
  - Critical (Phishing): Red (`#ef4444`)
  - Warning: Orange (`#f97316`)
  - Caution: Yellow (`#eab308`)
  - Safe: Green (`#10b981`)
- **Font**: Inter (Google Fonts)
- **Mode**: Dark by default

## API Endpoints

The frontend connects to the backend at `http://localhost:8000`:

- `POST /api/oauth/authorize` - Get OAuth authorization URL
- `POST /api/oauth/token` - Exchange OAuth code for token
- `GET /api/emails` - Fetch and analyze emails

## Environment Variables

Create a `.env` file in the frontend root (optional):

```env
VITE_API_URL=http://localhost:8000
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

MIT
