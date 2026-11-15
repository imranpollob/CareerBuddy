# CareerBuddy identity

The original mark combines an open C-shaped path with a forward arrow. The violet tile works on the app's light and dark surfaces. The wordmark is **CareerBuddy**, in Inter, with no trailing period.

- `careerbuddy-mark.svg`: master vector used by the sidebar, authentication, onboarding, assistant and learning views.
- `favicon-16.png`, `favicon-32.png`, `favicon-48.png`: browser-size exports. `/favicon.ico` contains all three frames.
- `icon-192.png`, `icon-512.png`: application icons referenced by `/site.webmanifest`.
- `icon-maskable-512.png`: opaque, mask-safe app icon.
- `/apple-touch-icon.png`: opaque 180px home-screen icon.

Update the master SVG, then run `node scripts/generate_brand_icons.mjs` from the repository root to regenerate the raster and ICO exports. It uses the project's existing Chrome/Playwright installation and makes no network requests. Run the frontend build afterward.

The reusable UI components are in `frontend/src/components/Brand.tsx`. The app manifest supplies icons and naming; no offline capability or service worker is introduced.
