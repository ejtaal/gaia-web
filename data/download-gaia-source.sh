#!/bin/bash

. ~/scripts/generic-linux-funcs.sh

DOWNLOADED=0
MAX_DOWNLOAD="$1"

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
            row_count="$(sqlite3 "$sqlite_db" 'select count(*) from gaia_source_filtered' | grep -oP '^\d+')"
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
        if check_sqlite_db "$sqlite_db" 100000; then
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
        GZIP_OK=n
        MD5_OK=y
        if gzip -t "$filename"; then
            hm + gzip checks out ok
            GZIP_OK=y
        fi
        if [ "$(md5sum "$filename" | cut -f 1 -d ' ')" = "$md5_sum" ]; then
            hm + md5sum checks out ok
            MD5_OK=y
        fi
        if [ "$GZIP_OK" = y -a "$MD5_OK" = y ]; then
            hm + "Processing file"
            ./gaia-process-csv.py "$filename"
            if check_sqlite_db "$sqlite_db" 100000; then
                hm + "Got row_count > 100000, seems in order."
                rm -vf "$filename"
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
        # WGET_OPTIONS="--limit-rate=1M"
        download_if_not_older "$filename" "$MAX_CACHE_AGE" "${BASE_URL}${filename}" "$WGET_OPTIONS"
        DOWNLOADED=$((DOWNLOADED+1))
        ./gaia-process-csv.py "$filename"
        # crud_js_from_sqlite "$sqlite_db" "$js_file"
        # csv.gz file should be able to be deleted now
        rm -vf "$filename"
        if [ -n "$MAX_DOWNLOAD" -a "$DOWNLOADED" -ge "$MAX_DOWNLOAD" ]; then
            hm - "Downloaded the maximum of $MAX_DOWNLOAD files"
            exit 0
        else
            hm + "Downloaded $DOWNLOADED files so far."
            exit 5
        fi

    fi
    hm - "Sleeping ${SLEEP}s..."
    # exit 7
    sleep $SLEEP
done
