#!/bin/bash

:||cat<<EOF
	JS_FILE="data/wp-open-clusters.js"
	CSV_FILE="data/wp-open-clusters.csv"
	# PREFIX="var wp_open_clusters = ["
	# echo "$PREFIX" > "$FILE"
	PAGE_NAME='List_of_open_clusters'
	URL="https://en.wikipedia.org/wiki/${PAGE_NAME}"
	API_URL="https://en.wikipedia.org/w/api.php?action=parse&format=json&page=${PAGE_NAME}&prop=text&formatversion=2"
	
	LYNX_DUMP_FILE="wp-open-clusters.table.txt"
	WP_EXPORT_FILE="wp-open-clusters.table.tsv"
	#wget -O export.json "$API_URL"
	#wget -O page.html "$URL"
	#lynx -dump -width=1023 "$URL" > lynx.dump.txt

	# export IFS='|'
	cat "$LYNX_DUMP_FILE" \
	| perl -p -e 's/\[\d+\]//g' \
	| grep '\^h' \
	| perl -p -e 's/^\s+(.*?)\s(\d+\^h.*?\^m)\s(.*?\d+°\s*\d+.*?)\s[\w\s]*?(\d+,*\d+)\s.*$/\4|\2|\3|\1/' \
	| grep '|' \
	| perl -pe 's/,(\d{3}|)/\1/' \
	| sort -n \
	| cat > "$WP_EXPORT_FILE"
EOF


	CSV_FILE="./wp-globular-clusters.csv"
	PAGE_NAME='List_of_globular_clusters'
	URL="https://en.wikipedia.org/wiki/${PAGE_NAME}"
	API_URL="https://en.wikipedia.org/w/api.php?action=parse&format=json&page=${PAGE_NAME}&prop=text&formatversion=2"
	
	LYNX_DUMP_FILE="wp-globular-clusters.table.txt"
	WP_EXPORT_FILE="wp-globular-clusters.table.tsv"
	#wget -O export.json "$API_URL"
	#wget -O page.html "$URL"
	# lynx -dump -width=1023 "$URL" > "$LYNX_DUMP_FILE"

	# export IFS='|'
	cat "$LYNX_DUMP_FILE" \
	| perl -p -e 's/\[\d+\]//g' \
	| grep '\^h' \
	| perl -p -e 's/^\s+(.*?)\s(\d+\^h.*?\^s)\s(.*?\d+°\s*\d+.*?″)\s.*?([\d\.]+)[^\d+]*$/\4|\2|\3|\1\n/' \
	| grep '|' \
	| sed '/Balbinot 1/q' \
	| sort -n \
	| perl -pe 's/\.(\d)\|/\1ZZ|/' \
	| perl -pe 's/\.(\d\d)\|/\1Z|/' \
	| perl -pe 's/^(\d+)\|/\1ZZZ|/' \
	| perl -pe 's/ZZZ\|/000|/' \
	| perl -pe 's/ZZ\|/00|/' \
	| perl -pe 's/Z\|/0|/' \
	| cat > "$WP_EXPORT_FILE"
	# | cat
	# | perl -pe 's/\.(\d\d)|/\1Z|/' \
	# | perl -pe 's/^(\d+)|/\1ZZZ|/' \
	# | sort -n \
	# | perl -p -e 's/^\s+(.*?)\s(\d+\^h.*?\^m)\s(.*?\d+°\s*\d+.*?)\s[\w\s]*?(\d+,*\d+)\s.*$/\4|\2|\3|\1/' \
	# | grep '|' \
	# | perl -pe 's/,(\d{3}|)/\1/' \
	

# | less
# echo | while read ra dec dist name; do
# 	#echo ra dec dist name = [$ra] [$dec] [$dist] [$name]
# 	arr_row="[ $(./sky-coords.py -pc "$ra" "$dec" "$dist"), \"$name\"],"
# 	echo "$arr_row" | tee -a "$FILE"
# 	#exit 5
# done
# echo "];" >> "$FILE"
#| perl -p -e 's/\s(\d+\^h.*^m)\s(.\d+°\s*\d+.*?)\s[\w\s]+(\d+,*\d+)\s.*$/|\1|\2\3/'
#| tr − - \
