# Blank Debian 13 box for the team, reachable over SSH. Logins come from passwords.txt (see README.md).
FROM debian:trixie-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      openssh-server sudo ca-certificates curl git nano vim-tiny less procps iputils-ping tmux \
      python3 python3-venv python3-pip build-essential \
 && rm -rf /var/lib/apt/lists/* \
 && rm -f /etc/ssh/ssh_host_* \
 && groupadd devbox

COPY sshd_devbox.conf /etc/ssh/sshd_config.d/devbox.conf
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 22
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
