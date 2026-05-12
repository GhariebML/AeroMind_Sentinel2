# Highway video background

Place real highway footage here as:

```text
public/videos/highway-demo.mp4
```

The React simulation has a **Video BG** toggle. If `highway-demo.mp4` exists, it will play as the dashboard background. If it is missing, the UI automatically falls back to the animated synthetic highway canvas so demos never break.

Recommended encoding:

- MP4 / H.264
- 1920x1080 or 1280x720
- 10-25 seconds loop
- Muted, no audio required
- Optimized for web (<20 MB if possible)
