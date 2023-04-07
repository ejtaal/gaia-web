#!/bin/bash

. ~/scripts/generic-linux-funcs.sh

SOURCE=http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/

MAX_CACHE_AGE=$((999*23*60))

BASE_URL="http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/"
MD5_URL="http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/_MD5SUM.txt"
MD5_FILE=MD5SUM.txt

download_if_not_older "MD5SUM.txt" "$MAX_CACHE_AGE" "$MD5_URL"

count=0
count_total="$(fgrep -c GaiaSource_ MD5SUM.txt)"

fgrep GaiaSource_ MD5SUM.txt \
| while read md5_sum filename; do
    count=$((count+1))
    hm \* "-> $filename $count/$count_total  ($md5_sum)"
    if [ -f "$filename" ]; then
    hm \* "   $filename found, checking ..."
        if gzip -t "$filename"; then
            hm + gzip checks out ok
        fi
        if [ "$(md5sum "$filename" | cut -f 1 -d ' ')" = "$md5_sum" ]; then
            hm + md5sum checks out ok
        fi
    else
        # Only download if not fully imported ok already
        download_if_not_older "$filename" "$MAX_CACHE_AGE" "${BASE_URL}${filename}"
    fi
    hm - "Sleeping 10s..."
    sleep 10
done