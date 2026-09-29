#!/bin/sh
set -e
NTFY_DATA_DIR="/var/lib/ntfy"
AUTH_DB="${NTFY_DATA_DIR}/auth.db"
USER_PROVISIONED_FLAG="${NTFY_DATA_DIR}/.users_provisioned"
echo "[ntfy-init] Checking if users need provisioning..."
for i in $(seq 1 30); do
    if [ -f "$AUTH_DB" ]; then
        echo "[ntfy-init] Auth database found"
        break
    fi
    echo "[ntfy-init] Waiting for ntfy to initialize... ($i/30)"
    sleep 2
done
if [ ! -f "$AUTH_DB" ]; then
    echo "[ntfy-init] ERROR: Auth database not found after 60 seconds"
    exit 1
fi
echo "[ntfy-init] Reconciling users and topic permissions..."
if [ -z "${NTFY_USERNAME:-}" ] || [ -z "${NTFY_PASSWORD:-}" ] || [ -z "${NTFY_SSO_PASSWORD:-}" ]; then
    echo "[ntfy-init] ERROR: publisher and SSO credentials must be set"
    exit 1
fi
if ntfy user list | grep -q "^user ${NTFY_USERNAME}"; then
    echo "[ntfy-init] User ${NTFY_USERNAME} already exists"
else
    echo "[ntfy-init] Creating user: ${NTFY_USERNAME}"
    printf "%s\n%s\n" "$NTFY_PASSWORD" "$NTFY_PASSWORD" | ntfy user add "$NTFY_USERNAME"
fi
if ntfy user list | grep -q '^user ntfy-sso '; then
    NTFY_PASSWORD="$NTFY_SSO_PASSWORD" ntfy user change-pass ntfy-sso
else
    NTFY_PASSWORD="$NTFY_SSO_PASSWORD" ntfy user add ntfy-sso
fi
echo "[ntfy-init] Granting access to webservices-* topics"
ntfy access "$NTFY_USERNAME" "webservices-alerts" write-only || true
ntfy access "$NTFY_USERNAME" "webservices-critical" write-only || true
ntfy access "$NTFY_USERNAME" "webservices-warnings" write-only || true
ntfy access ntfy-sso "webservices-alerts" read-write
ntfy access ntfy-sso "webservices-critical" read-write
ntfy access ntfy-sso "webservices-warnings" read-write
ntfy access ntfy-sso "*_alerts" read-write
echo "[ntfy-init] Granting access to test-* topics for integration tests"
ntfy access "$NTFY_USERNAME" "test-*" read-write || true
ntfy access ntfy-sso "test-*" read-write
touch "$USER_PROVISIONED_FLAG"
echo "[ntfy-init] User provisioning complete!"
ntfy user list
exit 0
