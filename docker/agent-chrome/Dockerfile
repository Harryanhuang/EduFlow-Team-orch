FROM debian:bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    chromium \
    fluxbox \
    fonts-liberation \
    fonts-noto-cjk \
    xvfb \
  && rm -rf /var/lib/apt/lists/*

# Docker Desktop on macOS does not provide the seccomp-bpf sandbox that
# Chromium requires, so --no-sandbox is necessary there. The container runs
# as an unprivileged 'chrome' user and is only reachable through the
# localhost-bound tcp-proxy published by docker-compose.yml.
RUN useradd -m -u 1000 chrome \
  && mkdir -p /data/profile /downloads \
  && chown -R chrome:chrome /data /downloads

USER chrome

EXPOSE 9222

CMD ["sh", "-lc", "rm -f /data/profile/Singleton* && Xvfb :99 -screen 0 1280x900x24 -nolisten tcp & env DISPLAY=:99 fluxbox >/tmp/fluxbox.log 2>&1 & exec env DISPLAY=:99 /usr/lib/chromium/chromium --disable-dev-shm-usage --no-sandbox --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 --user-data-dir=/data/profile --download-default-directory=/downloads about:blank"]
