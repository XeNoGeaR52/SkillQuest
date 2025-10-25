# SkillQuest Frontend - htmx Implementation

## Overview

This is a simple, interactive web frontend for the SkillQuest API built with **htmx** and **Tailwind CSS**. The frontend provides a complete user experience for the gamification platform with minimal JavaScript.

## Tech Stack

- **htmx 1.9.10** - Dynamic HTML interactions
- **Tailwind CSS** - Utility-first CSS framework (via CDN)
- **Jinja2** - Server-side templating
- **FastAPI** - Serves both API and HTML pages

## Project Structure

```
app/
├── web/                        # Web frontend module
│   ├── __init__.py
│   ├── routes.py              # Main page routes (dashboard, challenges, etc.)
│   ├── auth.py                # Authentication routes (login, register, logout)
│   └── deps.py                # Dependencies (auth helpers)
├── templates/                  # Jinja2 templates
│   ├── base.html              # Base layout with navigation
│   ├── dashboard.html         # User dashboard
│   ├── progress.html          # User progress page
│   ├── leaderboard.html       # Leaderboard page
│   ├── badges.html            # Badges gallery
│   ├── auth/
│   │   ├── login.html         # Login page
│   │   └── register.html      # Registration page
│   └── challenges/
│       ├── list.html          # Challenges list with filtering
│       └── detail.html        # Challenge detail with attempt submission
└── static/                     # Static assets
    ├── css/
    │   └── styles.css         # Custom CSS
    ├── js/
    │   └── app.js             # Minimal JavaScript utilities
    └── images/
        └── badges/            # Badge icons (if needed)
```

## Key Features

### Authentication
- **Cookie-based sessions** - JWT tokens stored in httpOnly cookies
- **Login/Register** - Simple forms with server-side validation
- **Auto-redirect** - Unauthenticated users redirected to login

### Pages

#### 1. Dashboard (`/`)
- User stats (XP, level, challenges completed)
- XP progress bar to next level
- Recent attempts and badges
- Quick action buttons

#### 2. Challenges (`/challenges`)
- Browse all published challenges
- Filter by difficulty (easy, medium, hard)
- Pagination support
- Card-based layout with XP rewards

#### 3. Challenge Detail (`/challenges/{id}`)
- Full challenge description
- Start new attempt (htmx POST)
- Submit solution with score slider
- View previous attempts

#### 4. Progress (`/progress`)
- Detailed user statistics
- All earned badges with dates
- Recent activity history
- Success rate visualization

#### 5. Leaderboard (`/leaderboard`)
- Top 50 players ranked by XP
- Current user's rank highlighted
- Medal icons for top 3

#### 6. Badges (`/badges`)
- Gallery of all available badges
- Visual indication of earned vs locked badges
- Progress bar for completion
- Badge conditions displayed

### htmx Features Used

- **`hx-post`** - Form submissions without page reload
- **`hx-target`** - Specify where response should be inserted
- **`hx-swap`** - Control how content is swapped
- **`hx-trigger`** - Custom event triggers
- **Loading indicators** - Built-in htmx request indicators

### Styling

- **Dark theme** - Gaming-themed color scheme
- **Tailwind utilities** - Responsive, mobile-first design
- **Custom CSS** - Animations, transitions, and polish
- **Gradient backgrounds** - Eye-catching headers
- **Progress bars** - Visual XP and level progression

## API vs Web Routes

The application now serves **two types of routes**:

### API Routes (for programmatic access)
- Prefixed with `/api`
- Return JSON responses
- Examples:
  - `POST /api/auth/login` - Get JWT tokens
  - `GET /api/challenges` - List challenges (JSON)
  - `POST /api/attempts` - Create attempt (JSON)

### Web Routes (for browser access)
- No prefix (root level)
- Return HTML responses
- Examples:
  - `GET /login` - Login page (HTML)
  - `GET /challenges` - Challenges page (HTML)
  - `POST /challenges/{id}/start` - Start attempt (HTML response)

**Note:** API routes remain unchanged and can still be used by mobile apps or third-party integrations.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This includes the new `jinja2` dependency.

### 2. Run the Application

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Access the Frontend

Open your browser to:
- **Web UI**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs

## Usage Flow

### First Time Users

1. **Navigate to** http://localhost:8000/
2. **Redirect to** `/login` (not authenticated)
3. **Click** "Register" link
4. **Fill out** registration form
5. **Auto-login** and redirect to dashboard

### Authenticated Users

1. **Dashboard** - View stats and recent activity
2. **Browse Challenges** - Filter by difficulty
3. **Start Challenge** - Click "Start New Attempt" (htmx)
4. **Submit Solution** - Use score slider and submit (htmx)
5. **View Results** - Instant feedback on XP earned
6. **Check Progress** - See badges earned and stats
7. **Leaderboard** - Compare with other players

## htmx Interactions

### Example: Starting a Challenge

**User Action**: Click "Start New Attempt"

**htmx Request**:
```html
<form hx-post="/challenges/{id}/start" hx-target="#attempt-response">
    <button type="submit">Start New Attempt</button>
</form>
```

**Server Response** (HTML fragment):
```html
<div class="alert alert-success">
    Challenge started! Attempt ID: {uuid}
</div>
```

**Result**: Message displayed without page reload

### Example: Submitting a Solution

**User Action**: Move score slider, click "Submit Solution"

**htmx Request**:
```html
<form hx-post="/attempts/{id}/submit" hx-target="#submission-response">
    <input type="range" name="score" value="85">
    <textarea name="solution">...</textarea>
    <button type="submit">Submit</button>
</form>
```

**Server Response** (HTML fragment):
```html
<div class="alert alert-success">
    <strong>Passed!</strong><br>
    Score: 85/100<br>
    XP Awarded: 425<br>
    <a href="/progress">View Progress</a>
</div>
```

**Result**: Instant feedback, XP updated in database

## Customization

### Change Theme Colors

Edit [tailwind.config](urn:pwp:tailwind.config) in [base.html](app/templates/base.html:15-29):

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: '#your-color',
                secondary: '#your-color',
            }
        }
    }
}
```

### Add Custom Styles

Edit [app/static/css/styles.css](app/static/css/styles.css:1-157)

### Modify Templates

All templates extend [base.html](app/templates/base.html:1-79). Common changes:
- Update navigation in [base.html](app/templates/base.html:25-41)
- Customize page layouts in individual templates
- Add new components in `app/templates/components/`

## Benefits of htmx Approach

✅ **No build tools** - No npm, webpack, or bundlers
✅ **Minimal JavaScript** - htmx handles AJAX automatically
✅ **Server-side rendering** - Better SEO and initial load
✅ **Progressive enhancement** - Works without JavaScript
✅ **Easy maintenance** - Python developers can work on frontend
✅ **Fast development** - No API contract needed between frontend/backend
✅ **Small payload** - Only HTML, no large JS frameworks

## Security

- **httpOnly cookies** - Tokens not accessible via JavaScript
- **CSRF protection** - Built into FastAPI forms
- **SameSite cookies** - Prevents cross-site attacks
- **Password hashing** - bcrypt with salt
- **Input validation** - Server-side with Pydantic

## Performance

- **Partial updates** - Only changed DOM elements updated
- **No re-renders** - Unlike React/Vue component re-renders
- **CDN assets** - htmx and Tailwind from CDN
- **Static files** - CSS/JS cached by browser
- **Minimal JavaScript** - Smaller bundle size

## Future Enhancements

- [ ] Real-time leaderboard updates (WebSockets)
- [ ] Code editor for solution submission (CodeMirror)
- [ ] Markdown rendering for challenge descriptions
- [ ] Image uploads for avatars
- [ ] Toast notifications library
- [ ] Infinite scroll for challenges
- [ ] Dark/light mode toggle
- [ ] Mobile app (keep API for React Native/Flutter)

## Troubleshooting

### Templates not found
Ensure FastAPI can find the templates directory:
```python
templates = Jinja2Templates(directory="app/templates")
```

### Static files 404
Check the static files mount in [main.py](app/main.py:26):
```python
app.mount("/static", StaticFiles(directory="app/static"), name="static")
```

### htmx not working
1. Check browser console for errors
2. Verify htmx is loaded: `<script src="https://unpkg.com/htmx.org@1.9.10"></script>`
3. Check network tab for htmx requests

### Cookies not set
1. Verify `httponly=True` and `samesite="lax"`
2. Check browser privacy settings
3. Ensure using HTTP (not HTTPS) for local development

## Contributing

When adding new features:

1. Create route in `app/web/routes.py`
2. Create template in `app/templates/`
3. Use htmx for dynamic interactions
4. Follow existing patterns for consistency
5. Test authentication requirements

## Resources

- [htmx Documentation](https://htmx.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/)

---

**Enjoy building with SkillQuest!** 🚀
