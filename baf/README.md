# Baf (باف)

Static prototype. Open `index.html` in a browser (no build step).

```
index.html
css/style.css
js/data/   teachers.js (real data), demo.js (placeholder ratings: delete later), filters.js
js/        utils.js, state.js, profile.js, carousel.js, home.js, compare.js, app.js
assets/teachers/   <teacher-id>.jpg
```

Scripts are plain (non-module) files loaded in order, so keep the order in `index.html`.
Next steps: replace `js/data/*` with API calls, and add a backend (database, auth, review moderation).
