#!/bin/bash
# Creates one login per line of /config/users.txt ("username:password"), then runs the SSH server.
set -euo pipefail

mkdir -p /etc/ssh/keys /run/sshd
for type in ed25519 rsa; do
  key=/etc/ssh/keys/ssh_host_${type}_key
  [ -f "$key" ] || ssh-keygen -q -t "$type" -N "" -f "$key"
done

while IFS=: read -r user password || [ -n "$user" ]; do
  password=${password%$'\r'}  # tolerate a passwords.txt saved with Windows line endings
  [[ -z "$user" || "$user" == \#* ]] && continue
  if ! id "$user" >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash --groups devbox,sudo "$user"
  fi
  # Home folders persist in a volume; fix ownership if the user came back with a different uid.
  if [ "$(stat -c %u "/home/$user")" != "$(id -u "$user")" ]; then
    chown -R "$user:$user" "/home/$user"
  fi
  echo "$user:$password" | chpasswd
done < /config/users.txt

exec /usr/sbin/sshd -D -e
