# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

FROM gitea.tu.tsolo.net/tsolo/tsolo-freecad:1.0
COPY ./dist/cycax-freecad-worker.sh /app
RUN apt-get update; apt-get install -y xz-utils python3-xdg
RUN echo "/app/cycax-freecad-worker.sh /usr/bin/freecad" > defaults/autostart
