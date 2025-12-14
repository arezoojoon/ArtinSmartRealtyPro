#!/bin/sh
# Runtime environment variable injection for Vite apps

# Create env-config.js file with runtime environment variables
cat <<EOF > /usr/share/nginx/html/env-config.js
window.ENV = {
  VITE_API_URL: "${VITE_API_URL:-}"
};
EOF

echo "Environment configuration injected successfully"
cat /usr/share/nginx/html/env-config.js
