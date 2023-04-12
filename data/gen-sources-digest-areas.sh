#!/bin/bash

c() { printf "%s\n" "$@" | bc -l; }

OUTPUT="Gaia_element_areas.txt"
> "$OUTPUT"

cat GaiaSourceDigest.csv \
| tr , ' ' \
| tr -d '+' \
| grep -v "^File" \
| while read filename_fapec num_sources ra_min ra_max dec_min dec_max; do
    # This is not entirely accurate for polar coords but will suffice for now
    area_calc="((-1*$ra_min)+$ra_max)*((-1*$dec_min)+$dec_max)"
    area="$(c "$area_calc")"
    element_name="$(basename $filename_fapec .csv.fapec)"
    # echo "area_calc: $area_calc = $area"
    echo $area $element_name \
    | tee -a "$OUTPUT"
done
