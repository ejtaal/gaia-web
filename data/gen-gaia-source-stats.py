#!/usr/bin/env python3

import glob
import sqlite3
import traceback

import sys
sys.path.append('../')
from gaia_web_include import *

def get_sqlite3_count_star( db_filename, table_name, where_clause=''):
    conn = sqlite3.connect( db_filename)
    cur = conn.cursor()
    cur.execute( f"select count(1) from {table_name} {where_clause}")
    # cur.execute( f"select count(*) from {table_name} {where_clause}")
    rows = cur.fetchall()
    count_star = rows[0][0]
    return count_star

import statistics


def gen_data_set_index():
    global GAIA_WEB_DATA_SET_INDEX
    
    all_data_sets = {}
    
    for n in GAIAWEB_DATA_SETS.keys():
        all_data_sets[n] = 'stars'
        # all_data_sets.append( [ n, 'stars'])

    for n in GAIAWEB_BIN_SETS.keys():
        all_data_sets[n] = 'cubes'
        # all_data_sets.append( [ n, 'cubes'])
    
    
    print( all_data_sets)
    # print( np.array2string( all_data_sets))
    check_before_write( GAIA_WEB_DATA_SET_INDEX, 'var gaia_web_datasets = ' + str(all_data_sets))
    

def main():
    
    hm('Running stats ...')
    global GRAND_DB_FULLPATH
    global GRAND_DB_TABLENAME

    bigdb_conn = sqlite3.connect( GRAND_DB_FULLPATH)
    suitable_sets = []

    dataset_size_lower_limit = 1 * 10**6

    # dataset_size_limit = 10 * 10**6
    dataset_size_limit = 50 * 10**6

    # limit_triggered = False

    for px_over_err in [ 200, 150, 100, 80, 50, 40, 30, 20, 10, 5]:
        # 100k will capture whole galaxy, > 205k will capture Magallanic Clouds
        dist_px_limit = {}
        dist_limit_reached = False
        for dist in [ 500, 1000, 2000, 3000, 4000, 5000, 10000, 20000, 30000, 50000, 100000, 250000]:
            abs_mag_limit_triggered = False
            if dist_limit_reached:
                continue
            # hm( dist)
            for abs_mag in [ -7, -5, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 8, 10, 15]:
                if abs_mag_limit_triggered or dist_limit_reached:
                    continue

                COUNT_QUERY=f"""
                    WHERE dist < {dist} and px_over_err > {px_over_err} and abs_mag < {abs_mag}"""
                params = { 'px_over_err': px_over_err, 'dist': dist, 'abs_mag': abs_mag}
                # hm( f"Counting stars in parameter set {params} ...")
                '''
Index ordering research :

Index 1:
(px_over_err ASC NULLS LAST, dist ASC NULLS LAST, abs_mag ASC NULLS LAST)
runtime: 1h22m (searching up to 10^6 stars)

Index 2:
(px_over_err DESC NULLS FIRST, dist ASC NULLS LAST, abs_mag ASC NULLS LAST)
runtime: 1h27m (searching up to 10 * 10^6 stars)
runtime: (searching up to 50 * 10^6 stars)
                '''


                dataset_num = get_pg_count_star( GRAND_DB_TABLENAME, COUNT_QUERY)
                if ( px_over_err, abs_mag) in dist_px_limit:
                    if dist_px_limit[( px_over_err, abs_mag)] > (0.9 * dataset_num):
                        hm( f'dist_px_limit[( {px_over_err}, {abs_mag})] > 0.9 * {dataset_num:,} @ dist {dist}', '-')
                        # Not going to find any further stars so need to skip to next px_over_err
                        hm( f'Practical distance limit of px_over_err {px_over_err} reached at distance {dist}. Skipping to next parameter set.', '-')
                        dist_limit_reached = True
                        continue
                
                if dataset_num < dataset_size_lower_limit:
                    continue
                elif dataset_num > dataset_size_limit:
                    abs_mag_limit_triggered = True
                    hm( f'Size limit of {dataset_size_limit:,} stars reached. Skipping to next parameter set.', '-')
                else:
                    print( f"Parameter set {params} : {dataset_num:,} stars.")
                
                dist_px_limit[( px_over_err, abs_mag)] = dataset_num

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()