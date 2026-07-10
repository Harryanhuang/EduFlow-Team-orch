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

# The chrome user + Docker's default seccomp profile provide sufficient
# sandboxing, so --no-sandbox is intentionally omitted.
RUN useradd -m -u 1000 chrome \
  && mkdir -p /data/profile /downloads \
  && chown -R chrome:chrome /data /downloads

USER chrome

EXPOSE 9222

CMD ["sh", "-lc", "rm -f /data/profile/Singleton* && Xvfb :99 -screen 0 1280x900x24 -nolisten tcp & env DISPLAY=:99 fluxbox >/tmp/fluxbox.log 2>&1 & exec env DISPLAY=:99 /usr/lib/chromium/chromium --disable-dev-shm-usage --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 --user-data-dir=/data/profile --download-default-directory=/downloads about:blank"]
