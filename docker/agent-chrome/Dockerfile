FROM debian:bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    chromium \
    fluxbox \
    fonts-liberation \
    fonts-noto-cjk \
    novnc \
    websockify \
    x11vnc \
    xvfb \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 chrome \
  && mkdir -p /data/profile /downloads \
  && chown -R chrome:chrome /data /downloads

USER chrome

EXPOSE 9222 6080

CMD ["sh", "-lc", "rm -f /data/profile/Singleton* && Xvfb :99 -screen 0 1280x900x24 -nolisten tcp & env DISPLAY=:99 fluxbox >/tmp/fluxbox.log 2>&1 & x11vnc -display :99 -forever -shared -nopw -listen 0.0.0.0 -rfbport 5900 >/tmp/x11vnc.log 2>&1 & websockify --web=/usr/share/novnc 6080 localhost:5900 >/tmp/novnc.log 2>&1 & exec env DISPLAY=:99 /usr/lib/chromium/chromium --no-sandbox --disable-dev-shm-usage --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --remote-allow-origins='*' --user-data-dir=/data/profile --download-default-directory=/downloads about:blank"]
