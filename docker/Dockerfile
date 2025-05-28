# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

FROM tsolo.io/local/tsolo-freecad:1.0
COPY cycax-freecad-worker.sh /app
RUN apt-get update; apt-get install -y xz-utils
RUN echo "/app/cycax-freecad-worker.sh /usr/bin/freecad" > defaults/autostart
