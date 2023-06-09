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
import traceback
import sys

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

def write_bin_sets():
    hm('Writing bin sets ...')
    for bin_name in GAIAWEB_BIN_SETS.keys():
        hm( f'... bin set {bin_name} ...')

        # c = bigdb_conn.cursor()
        b = GAIAWEB_BIN_SETS[bin_name]

        bin_db_file = f'{BIN_DB_BASEPATH}/{bin_name}.sqlite'        

        conn = sqlite3.connect( bin_db_file)
        # quotes needed for dashes in table names.
        df = pd.read_sql_query( f'SELECT * FROM "{bin_name}"', conn)
        values = df[ b['what_field']].to_list()
        # print( values)
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
        df.sort_values( ['dist', 'x', 'y', 'z', 'color', 'abs_mag'], inplace=True, ignore_index=True)
        # print( 'avg: ', statistics. ( values))
        print(df)


        if not os.path.exists( f'{SET_JS_BASEPATH}{bin_name}'):
            os.mkdir( f'{SET_JS_BASEPATH}{bin_name}')


        js_prefix = 'var data = '
        df_write_gaia_set( bin_name, js_prefix, df, ['x','y','z',b['what_field']])

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
    

def gen_hip_tycho_star_names_labels():
    hipp_df = pd.read_csv( 'gaia-dr3-hipparcos-best-neighbour.csv', sep=',', index_col=False)
    hipp_hood_df = pd.read_csv( 'gaia-dr3-hipparcos-neighbourhood.csv', sep=',', index_col=False)
    tycho_df = pd.read_csv( 'gaia-dr3-tycho-best-neighbour.csv', sep=',', index_col=False)
    IAU_WGSN_common_df = pd.read_csv( 'Starname_etymologies_IAU_WGSN_common.csv', sep=',', index_col=False)
    IAU_WGSN_arabic_df = pd.read_csv( 'Starname_etymologies_IAU_WGSN_Arabic.csv', sep=',', index_col=False)
    SIMBAD_HIP_DR3_df = pd.read_csv( 'SIMBAD-NAME-HIP-DR3.txt', sep='|', index_col=False, comment='-')

    columns_to_keep = [
        # cns5_id,gj_id,component_id,n_components,primary_flag,gj_system_primary,gaia_edr3_id,hip_id,ra,dec,epoch,coordinates_bibcode,parallax,parallax_error,parallax_bibcode,pmra,pmra_error,pmdec,pmdec_error,pm_bibcode,rv,rv_error,rv_bibcode,g_mag,g_mag_error,bp_mag,bp_mag_error,rp_mag,rp_mag_error,g_mag_from_hip,g_mag_from_hip_error,g_rp_from_hip,g_rp_from_hip_error,g_mag_resulting,g_mag_resulting_error,g_rp_resulting,g_rp_resulting_error,g_rp_resulting_flag,j_mag,j_mag_error,h_mag,h_mag_error,k_mag,k_mag_error,jhk_mag_bibcode,w1_mag,w1_mag_error,w2_mag,w2_mag_error,w3_mag,w3_mag_error,w4_mag,w4_mag_error,wise_mag_bibcode
        'hip_id',
        'gaia_edr3_id',
        'ra',
        'dec',
        'parallax',
        'parallax_error',
        # '',
        # '',
    ]
    CNS5_main_df = pd.read_csv( 'CNS5.main.csv', sep=',', index_col=False, usecols=columns_to_keep)





    HIP_orig_1997_df = pd.read_csv( 'hip-orig-data.csv', sep=',', index_col=False)

    print( HIP_orig_1997_df)
    # HIP_orig_1997_df['dist'] = lightyear_p_parsec * 1 / (HIP_orig_1997_df['plx'] * 0.001)
    HIP_orig_1997_df.rename( columns={ 'v_mag': 'mag'}, inplace = True )
    HIP_orig_1997_df = pandas_calc_xyz( HIP_orig_1997_df)
    print( HIP_orig_1997_df)
    

    # Column name with dot in it is ill received by pandas :(. 
    # Rename offending column name and by using read_csv(header=0) to overwrite existing header names
    #HIP        Common Name    RA or equi   Dec or equi   Parall.     sPar   Hp obs   Hp Abs    V Abs
    cols = ['HIP', 'Common Name', 'RA or equi', 'Dec or equi', 'plx', 'sPar', 'Hp obs', 'Hp Abs', 'V Abs', '(B-V)', '(B-V)T',  '(V-I)', 'Spectrum']
    HIP_redux_2007_df = pd.read_csv( 'HIP-2007-data-redux.csv', sep=',', index_col=False, names=cols, usecols=cols[0:-1] , header=0)

    print( HIP_redux_2007_df)

    HIP_redux_2007_df.rename( columns={ 'RA or equi': "ra", 'Dec or equi': "dec", 'Parall.': 'plx', 'Hp obs': 'mag'}, inplace = True )
    # df['abs_mag'] = df['mag'] + 5 - 5 * np.log10( df['dist'] * lightyear_p_parsec)
    HIP_redux_2007_df = pandas_calc_xyz( HIP_redux_2007_df)
    print( HIP_redux_2007_df)          
    # Some magnitude values are not present in the HIP data (looks like due to negative parallax data), so fill with 0?
    HIP_redux_2007_df['abs_mag'].fillna( 0, inplace=True)


    # exit(7)

    SIMBAD_HIP = {}
    SIMBAD_NOHIP = {}
    simbad_obj_template = {
        'hip': 0,
        'name': '',
        'gaia_dr3': 0
    }
    last_oid = 0

    # for simbad_oidref, id in SIMBAD_HIP_DR3_df.to_records():
    for rec in SIMBAD_HIP_DR3_df.to_records():
        # print(rec)
        cur_oid = rec[1]
        if last_oid != cur_oid:
            if last_oid != 0:
                # print( simbad_obj)
                if simbad_obj['hip'] == 0:
                    SIMBAD_NOHIP[ simbad_obj['gaia_dr3']] = simbad_obj
                else:
                    SIMBAD_HIP[ simbad_obj['hip']] = simbad_obj
                    # exit(9)
            simbad_obj = copy.deepcopy( simbad_obj_template)

        id = rec[2]

        hip_match =      re.match('^HIP\s+(\d+)', id)
        name_match =     re.match('^NAME\s+(.*?)\s+$', id)
        gaia_dr3_match = re.match('^Gaia DR3\s+(\d+)', id)
        if hip_match:
            simbad_obj['hip'] = int( hip_match.group(1))
        if name_match:
            if simbad_obj['name'] == '':
                simbad_obj['name'] = name_match.group(1)
            else:
                simbad_obj['name'] += ' / ' + name_match.group(1)
        if gaia_dr3_match:
            simbad_obj['gaia_dr3'] = gaia_dr3_match.group(1)
        
        last_oid = cur_oid

    # Save the last object too
    if simbad_obj['hip'] == 0:
        SIMBAD_NOHIP[ simbad_obj['gaia_dr3']] = simbad_obj
    else:
        SIMBAD_HIP[ simbad_obj['hip']] = simbad_obj

    # pprint( SIMBAD_HIP)
    # pprint( SIMBAD_NOHIP)
    # exit(8)


    # print( hipp_df, tycho_df, IAU_WGSN_common_df, IAU_WGSN_arabic_df)

    hip_id_names = {}
    
    for tup in IAU_WGSN_arabic_df[ ['Proper Name', 'HIP']].values:
        # print(tup)
        if re.match( r'^\d+$', str(tup[1])):
            hip_id_names[ tup[1]] = tup[0]

    # print( hip_id_names)

    for tup in IAU_WGSN_common_df[ ['Proper Name', 'HIP']].values:
        # print(tup)
        if re.match( r'^\d+$', str(tup[1])):
            if int(tup[1]) in hip_id_names:
                hip_id_names[ int(tup[1])] += ' / ' + tup[0]
            elif  tup[1] in hip_id_names:
                hip_id_names[ tup[1]] += ' / ' + tup[0]
            else:
                hip_id_names[ tup[1]] = tup[0]

    # print( hip_id_names)

    # exit(8)

    gaia_sid_name = {}

    '''
    So there are a few different cases that can occur:
    1. HIP number is in Gaia HIP reference table
    1.1 the source_id is in our DB with x,y,z -> use
    1.2 the source_id is not our DB with x,y,z -> calculate based on HIP RA, dec, parallax
    2. HIP number is not in Gaia HIP reference
    2.1 HIP with DR3 value known by SIMBAD
    2.1.1 the source_id is in our DB with x,y,z -> use
    2.1.2 the source_id is not our DB with x,y,z -> calculate based on HIP RA, dec, parallax
    2.2 SIMBAD doesn't know DR3 either -> calculate based on HIP RA, dec, parallax
    3. HIP not known by SIMBAD -> calculate based on HIP RA, dec, parallax
    '''

    hip_keys_gaia_xyz_resolved = []
    hip_keys_gaia_xyz_not_resolved = []
    hip_resolved_objects = []
    hip_resolved_labels = []
    grand_gaia_source_objects_names = []


    # hip_object_

    hip_names_xyz_df = pd.DataFrame()

    # TODO: Add names from SIMBAD where HIP numbers are known    

    # print( CNS5_main_df)
    # exit(8)

    # all_hip_keys = hip_id_names.keys()
    # all_hip_keys = all_hip_keys

    for hip_key in list( hip_id_names.keys()) + list( SIMBAD_HIP.keys()):
        if hip_key in hip_id_names:
            best_name_to_use = hip_id_names[ hip_key]
        else:
            best_name_to_use = SIMBAD_HIP[ hip_key]['name']

        gaia_sid = hipp_df[hipp_df['original_ext_source_id'] == int(hip_key)]['source_id'].values
        gaia_sid_dr3 = 0
        gaia_dr3_resolved = False
        gaia_dr3_xyz_resolved = False
        if len(gaia_sid) > 0:

            gaia_sid_name[ gaia_sid[0]] = best_name_to_use
            gaia_sid_dr3 = gaia_sid[0]
            gaia_dr3_resolved = True
            print( 'DR3 HIT', hip_key, gaia_sid, best_name_to_use )
        else:
            print( 'MISS', hip_key, best_name_to_use )
            if hip_key in SIMBAD_HIP:
                simbad_name = SIMBAD_HIP[ hip_key]
                if SIMBAD_HIP[ hip_key]['gaia_dr3'] != 0:
                    print( 'BUT SIMBAD HIT', hip_key, SIMBAD_HIP[ hip_key]['gaia_dr3'], best_name_to_use )
                    gaia_sid_name[ SIMBAD_HIP[ hip_key]['gaia_dr3']] = best_name_to_use
                    gaia_sid_dr3 = SIMBAD_HIP[ hip_key]['gaia_dr3']
                    gaia_dr3_resolved = True
                else:
                    print( 'SIMBAD DR3 MISS ALSO', hip_key, best_name_to_use)
            else:
                print( 'SIMBAD HIP MISS ALSO?', hip_key, best_name_to_use)

        if gaia_dr3_resolved:
            where_clause = f'where source_id = {gaia_sid_dr3}'
            sql_q = f'select source_id,{SELECT_ROUNDED_PG_CLAUSE} FROM "{GRAND_DB_TABLENAME}" {where_clause}'
            # print(sql_q)
            results = prep_dbq_pydict( sql_q)
            # df = pd.read_sql_query( sql_q, conn)
            # print(results)
            # exit(8)
            if len(results) > 0:
                r = results[0]
                grand_gaia_source_objects_names.append(
                    [
                        float( round(r['x'], 1)),
                        float( round(r['y'], 1)),
                        float( round(r['z'], 1)),
                        # float( round(r['color'], 1)),
                        # float( round(r['abs_mag'], 1)),
                        best_name_to_use
                     ]
                )
                gaia_dr3_xyz_resolved = True
                # print( hip_resolved_objects)
                # exit(9)
            else:
                hip_keys_gaia_xyz_not_resolved.append( hip_key)

            # exit( 8)
        
        if not gaia_dr3_xyz_resolved:
            # Resolve it using:
            # a) HIP data redux (2007) if present (Sirius isn't for example)
            # b) HIP original data (1997) otherwise
            # print( 'HIP resolving:', hip_key)
            hip_redux_row = HIP_redux_2007_df[ HIP_redux_2007_df['HIP'] == int(hip_key)]
            if len(hip_redux_row) > 0:
                print( hip_redux_row)
                r = hip_redux_row
                # r['abs_mag'].values[0]
                hip_resolved_objects.append(
                    [
                        round( r['x'].values[0], 1),
                        round( r['y'].values[0], 1),
                        round( r['z'].values[0], 1),
                        round( r['(B-V)'].values[0], 1),
                        round( r['abs_mag'].values[0], 1)
                     ]
                )
                hip_resolved_labels.append(
                    [
                        round( r['x'].values[0], 1),
                        round( r['y'].values[0], 1),
                        round( r['z'].values[0], 1),
                        best_name_to_use
                    ]
                )
                # print( 'HIP redux HIT', hip_key, gaia_sid, hip_id_names[ hip_key] )
            else:
                # print( 'HIP redux MISS', hip_key, gaia_sid, hip_id_names[ hip_key] )
                hip_orig_row = HIP_orig_1997_df[ HIP_orig_1997_df['hip_no'] == int(hip_key)]
                if len( hip_orig_row) > 0:
                    # print( 'HIP orig HIT', hip_key, gaia_sid, hip_id_names[ hip_key] )
                    r = hip_orig_row
                    hip_resolved_objects.append(
                        [
                            round( r['x'].values[0], 1),
                            round( r['y'].values[0], 1),
                            round( r['z'].values[0], 1),
                            round( r['bv_color'].values[0], 1),
                            round( r['abs_mag'].values[0], 1)
                        ]
                    )
                    hip_resolved_labels.append(
                        [
                            round( r['x'].values[0], 1),
                            round( r['y'].values[0], 1),
                            round( r['z'].values[0], 1),
                            best_name_to_use
                        ]
                    )
                    # print( hip_resolved_objects)
                    # exit(9)
                else:
                    # print( 'HIP orig MISS', hip_key, gaia_sid, hip_id_names[ hip_key] )
                    # Honestly don't know what to do with this
                    pass

                # hip_keys_gaia_xyz_not_resolved.append( hip_key)
    # exit(0)
    simbad_gaia_dr3_but_no_hip_names = []

    for simbad_gaia_dr3_key in SIMBAD_NOHIP.keys():
        where_clause = f'where source_id = {simbad_gaia_dr3_key}'
        sql_q = f'select source_id,{SELECT_ROUNDED_PG_CLAUSE} FROM "{GRAND_DB_TABLENAME}" {where_clause}'
        # print(sql_q)
        results = prep_dbq_pydict( sql_q)
        # df = pd.read_sql_query( sql_q, conn)
        # print(results)
        # exit(8)
        if len(results) > 0:
            # print( 'SIMBAD DR3 grand_gaia_source HIT', simbad_gaia_dr3_key, SIMBAD_NOHIP[ simbad_gaia_dr3_key]['name'])
            r = results[0]
            simbad_gaia_dr3_but_no_hip_names.append(
                [
                    float( round(r['x'], 1)),
                    float( round(r['y'], 1)),
                    float( round(r['z'], 1)),
                    # float( round(r['color'], 1)),
                    # float( round(r['abs_mag'], 1)),
                    SIMBAD_NOHIP[ simbad_gaia_dr3_key]['name']
                    ]
            )
            # gaia_dr3_xyz_resolved = True
            # print( hip_resolved_objects)
            # exit(9)
        else:
            # simbad_gaia_dr3_but_no_hip_names.append( hip_key)
            # print( 'SIMBAD DR3 grand_gaia_source MISS', simbad_gaia_dr3_key, SIMBAD_NOHIP[ simbad_gaia_dr3_key]['name'])
            pass


    print( 'all resolved HIP objects:')
    
    # pprint( hip_resolved_objects)
    cols = ['x','y','z','color','mag']
    hip_resolved_objects_df = pd.DataFrame( data = hip_resolved_objects, columns = cols)
    print( hip_resolved_objects_df)
    js_prefix = 'var hip_resolved_named_stars = '
    df_write_js_array( "hip_resolved_named_stars.js", js_prefix, hip_resolved_objects_df, cols)

    cols = ['x','y','z','name']
    
    hip_resolved_labels_df = pd.DataFrame( data = hip_resolved_labels, columns = cols)
    print( hip_resolved_labels_df)
    js_prefix = 'var hip_resolved_labels = '
    df_write_js_array( "hip_resolved_labels.js", js_prefix, hip_resolved_labels_df, cols)

    
    grand_gaia_source_objects_names_df = pd.DataFrame( data = grand_gaia_source_objects_names, columns = cols)
    print( grand_gaia_source_objects_names_df)
    js_prefix = 'var grand_gaia_source_objects_names = '
    df_write_js_array( "grand_gaia_source_objects_names.js", js_prefix, grand_gaia_source_objects_names_df, cols)

    
    # print( simbad_gaia_dr3_but_no_hip_names)
    simbad_gaia_dr3_but_no_hip_names_df = pd.DataFrame( data = simbad_gaia_dr3_but_no_hip_names, columns = cols)
    print( simbad_gaia_dr3_but_no_hip_names_df)
    js_prefix = 'var simbad_gaia_dr3_but_no_hip_names = '
    df_write_js_array( "simbad_gaia_dr3_but_no_hip_names.js", js_prefix, simbad_gaia_dr3_but_no_hip_names_df, cols)









    exit(0)

    exit(7)
    pprint( grand_gaia_source_objects_names)
    


        # else:
        #     # gaia_sid = tycho_df[tycho_df['tycho2tdsc_merge_oid'] == int(hip_key)]['source_id'].values
        #     # Try to look it up in tycho instead?
        #     if len(gaia_sid) > 0:
        #         gaia_sid_name[ gaia_sid[0]] = hip_id_names[ hip_key]
        #         print( hip_key, gaia_sid, hip_id_names[ hip_key] )
        #     else:
        #         print('no gaia sid found :(')
        # exit(9)

    exit(7)
    print(gaia_sid_name)
    # exit(9)

    where_clause = 'where source_id in ('
    for k in gaia_sid_name.keys():
        where_clause += str(k) + ','
    where_clause = where_clause[:-1]
    where_clause += ')'

    sql_q = f'select source_id,{SELECT_ROUNDED_PG_CLAUSE} FROM "{GRAND_DB_TABLENAME}" {where_clause}'
    print(sql_q)
    df = pd.read_sql_query( sql_q, conn)
    df['name'] = ''
    print(df)
    for k in gaia_sid_name.keys():
        df.loc[ df['source_id'] == k, 'name'] = gaia_sid_name[k]
        df.loc[ df['source_id'] == int(k), 'name'] = gaia_sid_name[int(k)]


    # tycho_df[tycho_df['tycho2tdsc_merge_oid'] == hip_key]['source_id']

    # gaia_coords = pd.read_sql
    df.sort_values( ['dist', 'x', 'y', 'z', 'color', 'abs_mag'], inplace=True, ignore_index=True)
    print(df)

    js_prefix = 'var star_labels = '
    df_write_js_array( "star-labels.js", js_prefix, df, ['x','y','z','name'])
    exit(0)
    
def gen_nebulae_set():
    # neb_df = pd.read_csv( '../nebulae/nenulae.tsv', sep='|', index_col=False, names=['dist_pc','ra_text','dec_text','name','stretch'] )
    neb_df = pd.read_csv( '../../gaia-web-data/nebulae/nebulae.tsv', sep='|', index_col=False)
    print( neb_df)
    neb_df['ra'] = neb_df.apply( lambda row: ra_text_to_deg( row['ra_text']), axis=1)
    neb_df['dec'] = neb_df.apply( lambda row: dec_text_to_deg( row['dec_text']), axis=1)
    neb_df['fieldradius_arcmins'] = neb_df.apply( lambda row: fr_text_to_deg( row['fieldradius_text']), axis=1)
    neb_df['dist_pc'] = neb_df['dist'] / lightyear_p_parsec
    neb_df['size_ly'] = np.sqrt(2) * neb_df['dist'] * np.tan( DEG2RAD * neb_df['fieldradius_arcmins'] / 60)
    neb_df = pandas_calc_xyz( neb_df)    
    # print( neb_df)
    print( neb_df[ ['dirname', 'ra_text', 'ra', 'dec_text', 'dec', 'size_ly']])

    df = neb_df[['x','y','z','size_ly','rotation_deg','dirname','name']]
    js_prefix = 'var nebula_data = '
    df_write_js_array( "nebula-data.js", js_prefix, df, ['x','y','z','name','size_ly','rotation_deg','dirname'])



def get_wp_open_cluster_set():

    wiki_df = pd.read_csv( 'wp-open-clusters.table.tsv', sep='|', index_col=False, names=['dist_pc','ra_text','dec_text','name','stretch'] )
    print( wiki_df)
    # df['result'] = df.apply(lambda row: multiply(row['column_1'], row['column_2']), axis=1)
    wiki_df['ra'] = wiki_df.apply( lambda row: ra_text_to_deg( row['ra_text']), axis=1)
    wiki_df['dec'] = wiki_df.apply( lambda row: dec_text_to_deg( row['dec_text']), axis=1)
    wiki_df['dist'] = wiki_df['dist_pc'] * lightyear_p_parsec
    wiki_df = pandas_calc_xyz( wiki_df)

    print( wiki_df)
    # exit(3)



    # df = pd.read_csv( 'wp-open-clusters.csv', header=1, quotechar='"', skipinitialspace = True, sep=',' )
    # df = pd.read_csv( 'wp-open-clusters.csv', quotechar='"', skipinitialspace = True, sep=',', index_col=False )
    df = wiki_df
    print( df)
    for a in ['lower', 'upper']:
        for b in ['x', 'y', 'z']:
            df[ f'{a}_{b}'] = 0

    min_interesting_radius = 150 #ly
    for col in ['x', 'y', 'z']:
        df.loc[ df[ col] < 0, f'lower_{col}'] = df[col] * 1.1 - min_interesting_radius
        df.loc[ df[ col] < 0, f'upper_{col}'] = df[col] * 0.9 + min_interesting_radius
        df.loc[ df[ col] > 0, f'lower_{col}'] = df[col] * 0.9 - min_interesting_radius 
        df.loc[ df[ col] > 0, f'upper_{col}'] = df[col] * 1.1 + min_interesting_radius 
    
    print( df)

    # Implement Dijkstra's algorithm for finding the shortest path:

    # Generate distance matrix
    distances = []
    # points = 
    # for p in range(0, len(df)):
    how_many_points = len( df)
    how_many_points = 40
    
    for p in range(0, how_many_points):
        new_row = []
        p_xyz = df.loc[ p, ['x','y','z']].values
        # print( p_xyz)
        # print( p_xyz[0])
        # exit(9)
        for q in range(0, how_many_points):
            if p == q:
                new_row.append(0)
            else:
                q_xyz = df.loc[ q, ['x','y','z']].values
                d = np.sqrt( (p_xyz[0]-q_xyz[0])**2 + (p_xyz[1]-q_xyz[1])**2 + (p_xyz[2]-q_xyz[2])**2 )
                new_row.append(d)
        # print( new_row)
        distances.append( new_row)
    # print( distances)

    # exact.solve_tsp_dynamic_programming
    # If you with for an open TSP version (it is not required to go back to the origin), just set all elements of the first column of the distance matrix to zero:

    # distance_matrix[:, 0] = 0
    np_dist = np.array(distances)
    np_dist[:, 0] = 0
    print( np_dist)

    # # Even with only 40 it eats RAM and CPU!
    from python_tsp.exact import solve_tsp_dynamic_programming
    from python_tsp.exact import solve_tsp_brute_force
    # permutation, distance = solve_tsp_dynamic_programming( np_dist)
    from python_tsp.heuristics import solve_tsp_simulated_annealing
    from python_tsp.heuristics import solve_tsp_local_search
    # permutation, distance = solve_tsp_local_search( np_dist)
    # permutation, distance = solve_tsp_brute_force( np_dist)
    
    # print( permutation, distance)
    # exit(9)





    # import dijkstra3d
    # # import numpy as np

    # field = np.ones((512, 512, 512), dtype=np.int32)
    # # field = df[ ['x','y','z'] ].to_records()[:40]
    # source = (0,0,0)
    # target = field[-1]
    # print( field)

    # # path is an [N,3] numpy array i.e. a list of x,y,z coordinates
    # # terminates early, default is 26 connected
    # path = dijkstra3d.dijkstra(field, source, target, connectivity=26) 

    # print( path)

    js_prefix = 'var wp_open_clusters = '
    df_write_js_array( "wp-open-clusters.js", js_prefix, df, ['x','y','z','name'])
    print('')

    # exit(1)
    # uplow_values = df[ ['lower_x', 'upper_x', 'lower_y', 'upper_y', 'lower_z', 'upper_z']].itertuples(index=False, name=None)
    uplow_values = list( df[ ['lower_x', 'upper_x', 'lower_y', 'upper_y', 'lower_z', 'upper_z']].to_records(index=False))
    print( uplow_values)

    sql_where = '''WHERE false
        '''
        # OR (dist > 8000)
        # OR (abs_mag < -5)
        # '''
    for r in uplow_values:
        sql_where += f"OR (x > {r[0]:.0f} AND x < {r[1]:.0f} and y > {r[2]:.0f} and y < {r[3]:.0f} and z > {r[4]:.0f} and z < {r[5]:.0f})\n"

    print( sql_where)

    sql_count = f"""SELECT count(1)
        FROM {GRAND_DB_TABLENAME}
        {sql_where}"""
    
    dataset_name = f"wp-open-clusters-{min_interesting_radius}ly"
    hm( f"Counting stars in set {dataset_name} ...")
    dataset_num = get_pg_count_star( GRAND_DB_TABLENAME, sql_where)

    hm( f"Dataset {dataset_name} has {dataset_num:,} stars.")

    hm( f"  ... Gaia-web dataset {dataset_name}, extracting from DB ...")

    SQL_QUERY=f"""SELECT 
    {SELECT_ROUNDED_PG_CLAUSE} 
    FROM {GRAND_DB_TABLENAME}
    {sql_where}"""

    # print( SQL_QUERY)
    df = pd.read_sql_query( SQL_QUERY, con=engine)
    print(df)
    # exit(5)
    # df[ 'dist'] = np.sqrt( df['x']**2 + df['y']**2 + df['z']**2)
    df.sort_values( ['dist', 'x', 'y', 'z', 'color', 'abs_mag'], inplace=True, ignore_index=True)
    # print( 'avg: ', statistics. ( values))
    print(df)

    if not os.path.exists( f'{SET_JS_BASEPATH}{dataset_name}'):
        os.mkdir( f'{SET_JS_BASEPATH}{dataset_name}')

    hm( f"  ... Gaia-web dataset {dataset_name}, writing to JS files ...")
    js_prefix = 'var data = '
    df_write_gaia_set( dataset_name, js_prefix, df, ['x','y','z','color','abs_mag'])
    print('')


    # print()
    # print()
    # print()

    # exit(2)


def main():
    
    gen_hip_tycho_star_names_labels()

    gen_nebulae_set()

    exit(8)

    # gen_data_set_index()

    # get_wp_open_cluster_set()

    # write_bin_sets()


    hm('Writing regular sets ...')
    global GRAND_DB_FULLPATH
    global GRAND_DB_TABLENAME
    # GRAND_GAIA_SOURCE_DB = f"{SOURCE_DB_PATH}/GrandGaiaSource.sqlite"

    # total_rows_in_sources = 127849797
    # total_rows_in_sources = 49426859
    # hm( f'total_rows_in_sources = {total_rows_in_sources:,}')

    # grand_total_rows = 0
    # try:
    #     hm( f'Counting stars in {GRAND_DB_FULLPATH} table grand_gaia_source ...')
    #     row_count = get_sqlite3_count_star( GRAND_DB_FULLPATH, GRAND_DB_TABLENAME)
    #     grand_total_rows = row_count
    # except:
    #     exit(1)
    #     pass
    # finally:
    #     # print( 'grand total: ', grand_total_rows)
    #     pass

    # hm( f"Total source star count matches grand DB: {total_rows_in_sources:,}", '+')

    # bigdb_conn = sqlite3.connect( GRAND_DB_FULLPATH)
    suitable_sets = []

    for dataset_name in GAIAWEB_DATA_SETS.keys():

        COUNT_QUERY=f"""SELECT count(1)
        FROM {GRAND_DB_TABLENAME}
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

        hm( f"Counting stars in set {dataset_name} ...")
        dataset_num = get_pg_count_star( GRAND_DB_TABLENAME, GAIAWEB_DATA_SETS[dataset_name])

        hm( f"Dataset {dataset_name} has {dataset_num:,} stars.")
        size_limit = 50 * 10**6
        if ( dataset_num > size_limit):
            hm( f'More than {size_limit:,} stars, adjust query to reduce size:\n{COUNT_QUERY}', '-')
        else:
            hm( "Suitable for a dataset, saving to list for extraction.", '+')
            suitable_sets.append( dataset_name)

    hm( f"Extracting datasets ...")
    for dataset_name in suitable_sets:
        hm( f"  ... Gaia-web dataset {dataset_name}, extracting from SQlite ...")

        SQL_QUERY=f"""SELECT 
        {SELECT_ROUNDED_PG_CLAUSE} 
        FROM {GRAND_DB_TABLENAME}
        {GAIAWEB_DATA_SETS[dataset_name]}"""

        print( SQL_QUERY)
        df = pd.read_sql_query( SQL_QUERY, con=engine)
        print(df)
        # exit(5)
        # df[ 'dist'] = np.sqrt( df['x']**2 + df['y']**2 + df['z']**2)
        df.sort_values( ['dist', 'x', 'y', 'z', 'color', 'abs_mag'], inplace=True, ignore_index=True)
        # print( 'avg: ', statistics. ( values))
        print(df)

        if not os.path.exists( f'{SET_JS_BASEPATH}{dataset_name}'):
            os.mkdir( f'{SET_JS_BASEPATH}{dataset_name}')

        hm( f"  ... Gaia-web dataset {dataset_name}, writing to JS files ...")
        js_prefix = 'var data = '
        df_write_gaia_set( dataset_name, js_prefix, df, ['x','y','z','color','abs_mag'])
        # exit(8)

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
