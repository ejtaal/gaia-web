#!/usr/bin/env python3

def hm( msg, pre = '*'):
    # Hacker message, what else ;)
    CYAN = '\033[96m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    RED = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'
    if pre == '!': msg = f"{RED}[{pre}] {msg}"
    elif pre == '+': msg = f"{GREEN}[{pre}] {msg}"
    elif pre == '-': msg = f"{YELLOW}[{pre}] {msg}"
    else: msg = f"{CYAN}[{pre}] {msg}"
    print( f"{BOLD}{msg}{ENDC}")
    



import glob
import sqlite3
import pandas as pd
import traceback
import sys
import numpy as np

from alive_progress import *
config_handler.set_global( length=60, spinner='classic', enrich_print = False, file = sys.stderr, force_tty = True)

sys.path.append('../')
from gaia_web_include import *

def get_sqlite3_count_star( db_filename, table_name, where_clause=''):
    conn = sqlite3.connect( db_filename)
    cur = conn.cursor()
    # cur.execute( f"select count(1) from {table_name}")
    cur.execute( f"select count(*) from {table_name} {where_clause}")
    rows = cur.fetchall()
    count_star = rows[0][0]
    return count_star

def update_grand_db( grand_db, source_db):

    bigdb_conn = sqlite3.connect( grand_db)
    # print( sqlite_db)
    cnx = sqlite3.connect( source_db)
    # This is ok as there should only be up to 500k rows in it per file
    df = pd.read_sql_query("SELECT * FROM 'gaia_source_filtered'", cnx)
    # print( df)

    # for source_id in [ 0, -1]:
    # Check if first and last source_id are present in the grand_gaia_source
    # if get_sqlite3_count_star( grand_db, GRAND_DB_TABLENAME, f'where source_id={df['source_id'].iloc[ 0]}')
    #     and get_sqlite3_count_star( grand_db, GRAND_DB_TABLENAME, f'where source_id={df['source_id'].iloc[ -1]}'):
    #     hm( "First and last source_id's already present, skipping", '+')                        
    #     continue
    # else:
    #     hm( "First and last source_id's not present, calculating data and adding ...")                        

    DEG2RAD = np.pi / 180;
    lightyear_p_parsec = 3.261563777
    # var wstream = fs.createWriteStream('stars.bin');
    # db.each(`SELECT ${fields.join(',')} from stars where parallax > 0`, function(err, row) {
    # df = filtered_stars
    print("[+] Calculating distances in lightyears ...")
    df['dist'] = lightyear_p_parsec * 1 / (df['parallax'] * 0.001)
    print("[+] Calculating x,y,z's ...")
    df['x'] = np.cos( df['ra'] * DEG2RAD) * np.cos( df['dec'] * DEG2RAD) * df['dist']
    # print("[+] Calculating y's ...")
    df['y'] = np.sin( df['ra'] * DEG2RAD) * np.cos( df['dec'] * DEG2RAD) * df['dist']
    # print("[+] Calculating z's ...")
    df['z'] = np.sin( df['dec'] * DEG2RAD) * df['dist']

    df['px_over_err'] = df['parallax'] / df['parallax_error']

    # Calc absolute magnitude
    # // M = m +5-5log10​(D)
    # // where:
    # //   M - Absolute magnitude
    # //   m – Apparent magnitude of the star; and
    # //   D – Distance between the star and Earth, measured in parsecs.
    df['abs_mag'] = df['mag'] + 5 - 5 * np.log10( df['dist'] * lightyear_p_parsec)

    filtered_stars = df
    save_db_stars = filtered_stars[ ['source_id', 'px_over_err', 'x', 'y', 'z', 'dist', 'color', 'abs_mag']]
    # save_db_stars = filtered_stars[ [ 'x', 'y', 'z', 'color', 'abs_magnitude']]
    # print( filtered_stars)
    # print( save_db_stars)
    # exit(8)


    print( f"[+] Writing filtered stars to {grand_db} ...")
   
    # added_to_db = 0
    try:
        save_db_stars.to_sql( GRAND_DB_TABLENAME, bigdb_conn, if_exists='append', index=False)
        return len(save_db_stars)
        # exit(4)
    except sqlite3.IntegrityError as e:
        hm( f'file {source_db}, seems loaded already (integrity error).','-')
        # print('_', end='')
        # print('INTEGRITY ERROR\n')
        # print(traceback.print_exc())
        return 0
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
    finally:
        pass

    # exit(7)
    
    cnx.close()

# Import statistics Library
import statistics

# Calculate middle values
# print(statistics.median([1, 3, 5, 7, 9, 11, 13]))
# print(statistics.median([1, 3, 5, 7, 9, 11]))
# print(statistics.median([-11, 5.5, -3.4, 7.1, -9, 22])) 


def main():
    
    for bin_name in GAIAWEB_BIN_SETS.keys():
        # c = bigdb_conn.cursor()
        b = GAIAWEB_BIN_SETS[bin_name]

        bin_db_file = f'{BIN_DB_BASEPATH}/{bin_name}.sqlite'        
        conn = sqlite3.connect( bin_db_file)
        df = pd.read_sql_query( f'SELECT * FROM {bin_name}', conn)
        values = df[ b['what_field']].to_list()
        print( values)
        preview_array( sorted( values))
        # If these don't vary much then use either, else use median?
        print( 'median: ', statistics.median( values))
        print( 'avg: ', statistics.mean( values))
        minv = min( values)
        maxv = max( values)
        avg = statistics.mean( values)
        print(df)
        df[ b['what_field'] ] = (df[ b['what_field']] - minv) / (maxv - minv)
        df[ 'dist'] = np.sqrt( df['x']**2 + df['y']**2 + df['z']**2)
        df.sort_values( 'dist', inplace=True, ignore_index=True)
        # print( 'avg: ', statistics. ( values))
        print(df)


        if not os.path.exists( f'{SET_JS_BASEPATH}{bin_name}'):
            os.mkdir( f'{SET_JS_BASEPATH}{bin_name}')

        pd.set_option( 'display.max_columns',  1000)
        pd.set_option( 'display.width',       32000)
        np.set_printoptions(threshold=np.inf)
        np.set_printoptions(suppress=True)
        # not working or only if lines become too long, not for joining them together?
        np.set_printoptions( linewidth = 120)

        size = len( df)
        for element_idx in range( 0, 100):
            start = int(element_idx / 100 * size)
            stop = int((element_idx + 1) / 100 * size) - 1
            # print( 'stop/start: ', start, stop)
            # print( df.iloc[start:stop+1])
            # Is that some old style string formatting??
            js_array = np.array2string( df[['x','y','z',b['what_field']]].iloc[start:stop+1].values
                , precision=3, separator=',' ,suppress_small=True
                , formatter={'float_kind':lambda x: "%d" % x if round(x) == x else "%.3f" % x }
                , max_line_width=120)
            # print( js_array)
            
            js_file = f'{SET_JS_BASEPATH}{bin_name}/{element_idx}.js'
            check_before_write( js_file, 'var data = ' + js_array)
        exit(8)


    global GRAND_DB_FULLPATH
    global GRAND_DB_TABLENAME
    # GRAND_GAIA_SOURCE_DB = f"{SOURCE_DB_PATH}/GrandGaiaSource.sqlite"

    # total_rows_in_sources = 127849797
    # total_rows_in_sources = 49426859
    # hm( f'total_rows_in_sources = {total_rows_in_sources:,}')

    grand_total_rows = 0
    try:
        hm( f'Counting stars in {GRAND_DB_FULLPATH} table grand_gaia_source ...')
        row_count = get_sqlite3_count_star( GRAND_DB_FULLPATH, GRAND_DB_TABLENAME)
        grand_total_rows = row_count
    except:
        exit(1)
        pass
    finally:
        # print( 'grand total: ', grand_total_rows)
        pass

    # print( 'grand total: ', grand_total_rows)

    if total_rows_in_sources == grand_total_rows or True:
        hm( f"Total source star count matches grand DB: {total_rows_in_sources:,}", '+')
    else:
        hm( f"Total star count in source DBs doesn't match grand DB total: {total_rows_in_sources:,} != {grand_total_rows:,}", '!')

        # hm('Updating the Grand DB ...')
        hm( 'Attempting to fill data from latest files ...')
    
        files_bar = alive_it(SQlite_db_files)
        for sqlite_db in files_bar:
            stars_added = update_grand_db( GRAND_DB_FULLPATH, sqlite_db)
            if stars_added > 0:
                row_count = get_sqlite3_count_star( GRAND_DB_FULLPATH, GRAND_DB_TABLENAME)
                grand_total_rows = row_count
                hm( f'Added {stars_added} from {sqlite_db}', '+')
            files_bar.text(f'Grand star count so far: {grand_total_rows:,} / {total_rows_in_sources:,}') 
            # files_bar.fin

        hm(f'Grand star count: {grand_total_rows:,} / {total_rows_in_sources}') 

        row_count = get_sqlite3_count_star( GRAND_DB_FULLPATH, GRAND_DB_TABLENAME)
        grand_total_rows = row_count

        if total_rows_in_sources == grand_total_rows:
            hm( f"Total source rows now match grand DB: {total_rows_in_sources:,}", '+')
        else:
            hm( f"Fatal error, total rows in source DBs still doesn't match grand DB total: {total_rows_in_sources:,} != {grand_total_rows:,}", '!')
            exit(1)
            hm('Updating the Grand DB ...')
            for sqlite_db in alive_it(SQlite_db_files):
                update_grand_db( GRAND_DB_FULLPATH, sqlite_db)

    bigdb_conn = sqlite3.connect( GRAND_DB_FULLPATH)

    for dataset_name in GAIAWEB_DATA_SETS.keys():
        hm( f"Generating Gaia-web dataset {dataset_name} ...")

        COUNT_QUERY=f"""SELECT count(1)
        FROM grand_gaia_source
        {GAIAWEB_DATA_SETS[dataset_name]}"""

        SQL_QUERY=f"""SELECT 
        {SELECT_ROUNDED_CLAUSE} 
        FROM grand_gaia_source
        {GAIAWEB_DATA_SETS[dataset_name]}"""

        # print( f"SQL_QUERY = {SQL_QUERY}")


        # dataset_df = pd.read_sql_query( SQL_QUERY, bigdb_conn)
        # dataset_num = len( dataset_df)

        '''
        The following limitations apply:
        - More than 10m stars will start to choke the rendering engine
        - More than 500Mb per file won't be cached by Cloudflare (too big a file anyway)
        - 100 files per set seems a reasonable coverage split
        Nice to have's:
        - Order data in increasing distance, will require index on dist column?
        - 
        '''

        hm( "Counting stars in this set...")
        dataset_num = get_sqlite3_count_star( GRAND_DB_FULLPATH, GRAND_DB_TABLENAME, GAIAWEB_DATA_SETS[dataset_name])

        hm( f"Dataset {dataset_name} has {dataset_num:,} stars.")
        if ( dataset_num > 5 * 10 **6):
            hm( f'More 5m star, adjust query to reduce size:\n{COUNT_QUERY}', '-')
        else:
            # Create 100 files of roughly equal size
            cur = bigdb_conn.cursor()
            cur.execute( SQL_QUERY);
            for row in cur:
                print( row)
                exit(9)
            # js_files = []
            # for file_index in range(1,101):
                """
                cursor.fetchall() fetches all results into a list first.
                Instead, you can iterate over the cursor itself:
                """
                
    # do_stuff_with_row

        # dataset_file = f"{SOURCE_DB_PATH}/{dataset_name}.js"
        
        # checking count first:
        # echo "var stars = [" > "$dataset_file"

        # for sqlite_db in GaiaSource_*.sqlite; do
        #     # Scan for count first? Maybe only in a single indexed db
        #     SQL_QUERY=f"""SELECT 
        #     {SELECT_ROUNDED} 
        #     FROM gaia_source_filtered
        #     {where_clause}"""
        #     sqlite3 "$sqlite_db" "$SQL_QUERY LIMIT 2" \
        #         | tr '|' , \
        #         | perl -pe '
        #         s/^/[/;
        #         s/$/],/;
        #         s/(\d\.\d{3})\d+/\1/g;
        #         s/(\d{3}\.\d)\d+/\1/g;
        #         s/(\d\.\d)\d+\]/\1]/;
        #         ' \
        #         | cat     >> "$dataset_file"
            
        #     exit 11
        # done
        # echo "];" >> "$js_out"

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()


    # count_star = get_sqlite3_count_star( sqlite_db, 'gaia_source_filtered')
    # total_rows_in_sources += count_star
    #print('.', end='')

"""
cursor.fetchall() fetches all results into a list first.
Instead, you can iterate over the cursor itself:
"""

if False:
    c.execute('SELECT * FROM big_table') 
    for row in c:
        pass
    # do_stuff_with_row


exit(3)



"""
conn = sqlite3.connect( sqlite_db)
save_db_stars.to_sql( 'gaia_source_filtered', conn, if_exists='replace', index=False)



count_total="$(fgrep -c GaiaSource_ MD5SUM.txt)"
count_present="$(ls -1 GaiaSource_*.sqlite | wc -l)"

if [ "$count_present" != "$count_total" ]; then
    hm ! "Not all DB files found: $count_present of $count_total only."
else
    hm \* "Not all DB files found: $count_present of $count_total only."
fi

hm "Checking DB files ..."
for sqlite_db in GaiaSource_*.sqlite; do
    row_count="$(sqlite3 "$sqlite_db" 'select count(*) from gaia_source_filtered' | grep -oP '^\d+')"
    if [ -z "$row_count" -o "0$row_count" -lt 100000 ]; then
        echo
        hm - "DB file sqlite_db : Got row_count of [$row_count], please investigate"
        exit 3
    else
        total_rows_in_sources=$((total_rows_in_sources+row_count))
        echo $total_rows_in_sources
        echo -n .
    fi
done

exit 5

GRAND_GAIA_SOURCE_DB="./GrandGaiaSource.sqlite"
hm \* "Checking/updating large gaia_source DB ..."
    row_count="$(sqlite3 "$GRAND_GAIA_SOURCE_DB" 'select count(*) from gaia_source_filtered_all' | grep -oP '^\d+')"


echo

exit 1

echo "$STAR_DATA_SETS" \
| while read dataset_name where_clause; do
done

exit 0

preview_file() {
    # Show file a la print( pandas.dataframe)
    file="$1"
    HUMAN_SIZE="$(ls -lh "$file" | awk '{ print $5}')"
    FILE_LINES="$(cat "$file" | wc -l)"
    echo "$(ls -l "$file") / $HUMAN_SIZE / $FILE_LINES l."
    head -3 "$file" | grep .
    echo ...
    tail -3 "$file" | grep .
}

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

SOURCE=http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/

MAX_CACHE_AGE=$((999*23*60))

BASE_URL="http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/"
MD5_URL="http://cdn.gea.esac.esa.int/Gaia/gdr3/gaia_source/_MD5SUM.txt"
MD5_FILE=MD5SUM.txt
SLEEP=60

download_if_not_older "MD5SUM.txt" "$MAX_CACHE_AGE" "$MD5_URL"

count=0

# fgrep GaiaSource_ MD5SUM.txt \

{   ls -1 GaiaSource_*csv.gz;
    grep -oP 'GaiaSource_.*' MD5SUM.txt | shuf; } \
| while read filename; do
    md5_sum="$(grep "$filename" MD5SUM.txt | cut -f 1 -d' ')"
    count=$((count+1))
    hm \* "-> $filename $count/$count_total  ($md5_sum)"

    sqlite_db="$(dirname $filename)/$(basename $filename .csv.gz).sqlite"
    js_file="$(dirname $filename)/$(basename $filename .csv.gz).js"

    if [ -f "$sqlite_db" ]; then
        hm + "SQlite db file $sqlite_db found, checking..."
        if [ ! -s "$sqlite_db" ]; then
            hm ! "SQlite db file $sqlite_db seems empty, deleting ..."
            rm -vf "$sqlite_db"
        else
            row_count="$(sqlite3 "$sqlite_db" 'select count(*) from gaia_source_filtered' | grep -oP '^\d+')"
            if [ -z "$row_count" -o "0$row_count" -lt 100000 ]; then
                hm - "Got row_count: [$row_count], please investigate"
                exit 3
            else
                hm + "Got row_count: [$row_count], seems in order."
                crud_js_from_sqlite "$sqlite_db" "$js_file"
                if [ -f "$filename" ]; then
                    hm + "Deleting source file: $filename"
                    rm -vf "$filename"
                fi
                continue
            fi
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
            crud_js_from_sqlite "$sqlite_db" "$js_file"
            # exit 1
        else
            hm ! "Deleting file, redownloading next time."
            rm -f "$filename"
            NEED_REDOWNLOAD=y
        fi
    fi

    if [ ! -f "$filename" ]; then
        # Only download if not fully imported ok already
        download_if_not_older "$filename" "$MAX_CACHE_AGE" "${BASE_URL}${filename}"
        DOWNLOADED=$((DOWNLOADED+1))
        ./gaia-process-csv.py "$filename"
        crud_js_from_sqlite "$sqlite_db" "$js_file"
        # csv.gz file should be able to be deleted now
        rm -f "$filename"
        if [ -n "$MAX_DOWNLOAD" -a "$DOWNLOADED" -ge "$MAX_DOWNLOAD" ]; then
            hm - "Downloaded the maximum of $MAX_DOWNLOAD files"
            exit 0
        else
            hm + "Downloaded $DOWNLOADED files so far."
        fi

    fi
    hm - "Sleeping ${SLEEP}s..."
    sleep $SLEEP
done
"""
