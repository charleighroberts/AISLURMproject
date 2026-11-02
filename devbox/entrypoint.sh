#!/bin/bash
# 1. One login per public key in /config/keys (<username>.pub).
# 2. A firewall: the box can reach the internet, but not the host PC, other containers, or the home network.
# 3. The SSH server runs without the permission to change that firewall, so not even sudo can undo it.
set -euo pipefail

mkdir -p /etc/ssh/keys /run/sshd
for type in ed25519 rsa; do
  key=/etc/ssh/keys/ssh_host_${type}_key
  [ -f "$key" ] || ssh-keygen -q -t "$type" -N "" -f "$key"
done

# Rebuilt on every start, so deleting someone's key file and restarting revokes their login.
rm -rf /etc/ssh/authorized_keys
mkdir -m 755 /etc/ssh/authorized_keys
for pub in /config/keys/*.pub; do
  [ -e "$pub" ] || continue
  user=$(basename "$pub" .pub)
  if [[ ! "$user" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
    echo "skipping $pub: file name must be a lowercase username" >&2
    continue
  fi
  id "$user" >/dev/null 2>&1 || useradd --create-home --shell /bin/bash --groups devbox "$user"
  usermod --password '*' "$user"  # no password at all
  # Home folders persist in a volume; fix ownership if the user came back with a different uid.
  if [ "$(stat -c %u "/home/$user")" != "$(id -u "$user")" ]; then
    chown -R "$user:$user" "/home/$user"
  fi
  tr -d '\r' < "$pub" > "/etc/ssh/authorized_keys/$user"
  chmod 644 "/etc/ssh/authorized_keys/$user"
  echo "login enabled: $user"
done

host_ip=$(getent ahostsv4 host.docker.internal | awk 'NR == 1 { print $1 }' || true)
# Docker's DNS forwards lookups to its upstream server from inside this box, and that server sits on a
# private address, so it gets a narrow exception: port 53 on that one address only.
dns_ips=$(grep -oE 'ExtServers: \[.*\]' /etc/resolv.conf | grep -oE '[0-9]+(\.[0-9]+){3}' || true)
iptables -F OUTPUT
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT  # replies to incoming SSH
for dns in ${dns_ips:-192.168.65.7}; do
  iptables -A OUTPUT -d "$dns" -p udp --dport 53 -j ACCEPT
  iptables -A OUTPUT -d "$dns" -p tcp --dport 53 -j ACCEPT
done
for net in ${host_ip:+$host_ip/32} 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 169.254.0.0/16; do
  iptables -A OUTPUT -d "$net" -j REJECT
done
if ip6tables -L OUTPUT >/dev/null 2>&1; then
  ip6tables -F OUTPUT
  ip6tables -A OUTPUT -o lo -j ACCEPT
  ip6tables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
  ip6tables -A OUTPUT -j REJECT
fi
echo "firewall: blocked host PC ($host_ip) and private networks; DNS via ${dns_ips:-192.168.65.7}"

exec capsh --drop=cap_net_admin -- -c 'exec /usr/sbin/sshd -D -e'
