#!/bin/bash

. ~/scripts/generic-linux-funcs.sh

DOWNLOADED=0
MAX_DOWNLOAD="$1"

# Minimum count of stars per DB to consider it downloaded & processed properly:
# Most have ~250 k but one had around 28k "only"
MIN_STAR_COUNT=20000

JS_WHERE_CLAUSE="where parallax / parallax_error > 5"

JS_INDEX="gaia-web-sky-elements.js"
update_js_file_index() {
    echo "var available_elements=[" > "$JS_INDEX"
    grep -l '^var stars =' *.js \
    | sed -e "s/^/'/" -e "s/.js$/',/" \
    | cat >> "$JS_INDEX"
    # for jsfile in *.js; do
    #     if head "$jsfile" | grep -q '^var stars ='; then
    #         echo "'$(basename $jsfile .js)'," >> "$JS_INDEX"
    #     fi
    # done
    echo "];" >> "$JS_INDEX"
    preview_file "$JS_INDEX"
}

crud_js_from_sqlite() {
    # split js files out in different slices:
    # Solar neighbourhood:
    # nearest 1000 lightyear
    # Galactic outline:
    # furthest 2,000 - 70,000 lightyear
    # select x, y, z, sqrt(x*x + y*y + z*z) as dist from gaia_source_filtered where dist < 160 limit 10;
    sqlitedb_file="$1"
    js_out="$2"

    db_count="$(sqlite3 "$sqlitedb_file" "select count(*) from gaia_source_filtered $JS_WHERE_CLAUSE")"
    line_count=0
    if [ -s "$js_out" ]; then
        line_count="$(cat $js_out | wc -l)"
    fi

    if [ "$db_count" = $((line_count-2)) ]; then
        hm + "JS file $js_out exists and corresponds with DB: $db_count lines."
        total_parsed_ok=$((total_parsed_ok+1))
    else
        hm - "JS file $js_out doesn't exist, or invalid line count. Re-generating ..."
        #  Generate the file:
        echo "var stars = [" > "$js_out"
        sqlite3 "$sqlitedb_file" \
        "select x,y,z,color,abs_magnitude from gaia_source_filtered
        $JS_WHERE_CLAUSE
        " \
        | tr '|' , \
        | perl -pe '
        s/^/[/;
        s/$/],/;
        s/(\d\.\d{3})\d+/\1/g;
        s/(\d{3}\.\d)\d+/\1/g;
        s/(\d\.\d)\d+\]/\1]/;
        ' \
        | cat     >> "$js_out"
        echo "];" >> "$js_out"

        hm + "JS file $js_out generated, line count: $(cat $js_out | wc -l)"
        # exit 1
    fi
    # Either way, db row count should be js_out line count - 2
    preview_file "$js_out"
    update_js_file_index

}

check_sqlite_db() {
    local sqlite_db="$1"
    local min_rows="$2"

    if [ -f "$sqlite_db" ]; then
        hm + "SQlite db file $sqlite_db found, checking..."
        if [ ! -s "$sqlite_db" ]; then
            hm ! "SQlite db file $sqlite_db seems empty, deleting ..."
            rm -vf "$sqlite_db"
        else
            sqlite3 "$sqlite_db" 'select count(*) from gaia_source_filtered'
            row_count="$(sqlite3 "$sqlite_db" 'select count(1) from gaia_source_filtered' | grep -oP '^\d+')"
            if [ -z "$row_count" -o "0$row_count" -lt "$min_rows" ]; then
                return 1
            else
                # crud_js_from_sqlite "$sqlite_db" "$js_file"
                # if [ -f "$filename" ]; then
                #     hm + "Deleting source file: $filename"
                #     rm -vf "$filename"
                # fi
                return 0
            fi
        fi
    fi
    
    return 1

}

SOURCE=http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/

MAX_CACHE_AGE=$((999*23*60))

BASE_URL="http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/"
MD5_URL="http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/_MD5SUM.txt"
MD5_FILE=MD5SUM.txt
SLEEP=60

download_if_not_older "MD5SUM.txt" "$MAX_CACHE_AGE" "$MD5_URL"

count=0
count_total="$(fgrep -c GaiaSource_ MD5SUM.txt)"


checkfile_cmd_hash() {
	local filename="$1"
	local test_cmd="$2"
	local file_hash="$3"

	# echo p | md5sum | wc -c
	case ${#file_hash} in
		32) hash_cmd=md5sum;;
		40) hash_cmd=sha1sum;;
		64) hash_cmd=sha256sum;;
		128) hash_cmd=sha512sum;;
		*) hm ! 'Unknown CRC hash specifief'
	esac

	ALL_OK_RT_CODE=1
	if [ -f "$filename" ] && $test_cmd "$filename"; then
		# Final check
    if [ "$($hash_cmd "$filename" | cut -f 1 -d ' ')" = "$file_hash" ]; then
			ALL_OK_RT_CODE=0
		fi
	fi
	return $ALL_OK_RT_CODE
}

# fgrep GaiaSource_ MD5SUM.txt \


# Download in order of angular size

sort -rn Gaia_element_areas.txt \
| grep -P 'GaiaSource_.*' \
| while read area element; do
    filename="${element}.csv.gz"
    # area="$(grep "$element" Gaia_element_areas.txt | cut -f 1 -d' ')"
    md5_sum="$(grep "$filename" MD5SUM.txt | cut -f 1 -d' ')"
    count=$((count+1))
    hm \* "-> $filename $count/$count_total (area: $area ~deg^2) (md5: $md5_sum)"

    sqlite_db="source/${element}.sqlite"
    # sqlite_db="$(dirname $filename)/$(basename $filename .csv.gz).sqlite"
    # js_file="$(dirname $filename)/$(basename $filename .csv.gz).js"

    # Check if at least 100k lines are present
    if [ -f "$sqlite_db" ]; then
        if check_sqlite_db "$sqlite_db" $MIN_STAR_COUNT; then
            hm + "Got row_count > 100000, seems in order."
            continue
        else
            hm - "Got less than 100000 rows, please investigate"
            exit 3
        fi
    fi

    # hm \* "Sleeping $SLEEPs..."
    # sleep $SLEEP
    # continue
    NEED_REDOWNLOAD=n
    if [ -f "$filename" ]; then
        hm + "   $filename found, checking ..."
				if checkfile_cmd_hash "$filename" 'gzip -t' "$md5_sum"; then
###         GZIP_OK=n
###         MD5_OK=y
###         if gzip -t "$filename"; then
###             hm + gzip checks out ok
###             GZIP_OK=y
###         fi
###         if [ "$(md5sum "$filename" | cut -f 1 -d ' ')" = "$md5_sum" ]; then
###             hm + md5sum checks out ok
###             MD5_OK=y
###         fi
###         if [ "$GZIP_OK" = y -a "$MD5_OK" = y ]; then
            hm + "Processing file"
            ./gaia-process-csv.py "$filename"
            if check_sqlite_db "$sqlite_db" $MIN_STAR_COUNT; then
                hm + "Got row_count > 100000, seems in order."
                rm -vf "$filename"
								continue
            else
                hm - "Got less than 100000 rows, please investigate"
                exit 3
            fi
        else
            hm ! "Deleting file, redownloading next time."
            rm -f "$filename"
            NEED_REDOWNLOAD=y
        fi
    fi

    if [ ! -f "$filename" ]; then
        # Only download if not fully imported ok already
        COMMON_WGET_OPTIONS="-q  --show-progress --progress=bar:force --tries=100" # For if we get throttled
				HOUR=$(date +%H)
				if date +%H | grep -qP '^(23|0?[0-7])$'; then
					hm + "Using quiet hour speed: 10M/s"
					WGET_OPTIONS="$COMMON_WGET_OPTIONS --limit-rate=2M"
				else
					hm - "Using busy hour speed: 500k/s"
					WGET_OPTIONS="$COMMON_WGET_OPTIONS --limit-rate=500k"
				fi
        download_if_not_older "$filename" "$MAX_CACHE_AGE" "${BASE_URL}${filename}" "$WGET_OPTIONS"
        DOWNLOADED=$((DOWNLOADED+1))

				if checkfile_cmd_hash "$filename" 'gzip -t' "$md5_sum"; then
					hm + "File gzip and md5 look ok"
				else
					hm - "File integrity failed. Try again next time."
        	rm -vf "$filename"
					continue
				fi
        ./gaia-process-csv.py "$filename" && \
        	rm -vf "$filename"
        if [ -n "$MAX_DOWNLOAD" -a "$DOWNLOADED" -ge "$MAX_DOWNLOAD" ]; then
            hm - "Downloaded the maximum of $MAX_DOWNLOAD files"
            exit 0
        else
            hm + "Downloaded $DOWNLOADED files so far."
        fi

    fi
    hm - "Sleeping ${SLEEP}s..."
    # exit 7
    sleep $SLEEP
done
