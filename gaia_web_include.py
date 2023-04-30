
import pandas as pd
import numpy as np
from pprint import pprint
import os
import re

from concurrent.futures import ProcessPoolExecutor

import sys
from alive_progress import *
config_handler.set_global( length=60, spinner='classic', enrich_print = False, file = sys.stderr, force_tty = True, precision = 2)
# Don't seem to work, hmm:
# stats (bool|str): [True] configures the stats widget (123.4/s, eta: 12s)
# ↳ send a string with {rate} and {eta} to customize it

DEG2RAD = np.pi / 180;

lightyear_p_parsec = 3.261563777

SOURCE_DB_PATH = "./source"
SET_JS_BASEPATH = "./set-"
GRAND_DB_FULLPATH = "./grand/Grand_gaia_source.sqlite"
GRAND_DB_TABLENAME = 'grand_gaia_source'

BIN_DB_BASEPATH = "./bins/"

GAIA_WEB_DATA_SET_INDEX = "./gaia-web-data-sets-index.js"

debug = False

def hm( msg, pre = '*', end = '\n'):
    # Hacker message, what else ;)
    CYAN = '\033[96m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    RED = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'
    if pre == '!': msg = f"{RED}[{pre}] {msg}"
    elif pre == '+': msg = f"{GREEN}[{pre}] {msg}"
    elif pre == '-': msg = f"{YELLOW}[{pre}] {msg}"
    else: msg = f"{CYAN}[{pre}] {msg}"
    print( f"{BOLD}{msg}{ENDC}", end = end)

def get_pgdb_pw( user):
    fn = f'~/.pgpass.{user}'
    pw = ''
    if not os.path.exists( os.path.expanduser( fn)):
        print( f"{fn} file not found!")
        exit( 1)
    with open( os.path.expanduser( fn)) as file:
        pw = file.readlines()[0]

    return(pw)


'''
Some wonderful PG routines crafted in the heat of battle with the DBs ;)
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy import select

db_pw = get_pgdb_pw('erik1').rstrip('\n')
# print(db_pw)

engine = create_engine( f'postgresql://erik1:{db_pw}@localhost:5432/gaiaweb')
# engine = create_engine( f'postgresql://erik1:{db_pw}@localhost:5432/gaiaweb', fast_executemany=True)
# engine = create_engine( f'postgresql://erik1:{db_pw}@localhost:5432/gaiaweb', executemany_mode='values_plus_batch')
# engine = create_engine( f'postgresql://erik1:{db_pw}@localhost:5432/gaiaweb', executemany_values_page_size = 500000, page_size = 500000)

# engine = create_engine( f'postgresql://erik1:{db_pw}@localhost:5432/gaiaweb', use_batch_mode = True)

# from sqlalchemy import event

# @event.listens_for(engine, 'before_cursor_execute')
# def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
#     if executemany:
#         cursor.fast_executemany = True
#         cursor.commit()


#import sqlalchemy as sa # To use sa.text() ?
import psycopg2
import psycopg2.extras # For DictCursor
conn = psycopg2.connect( f"dbname='gaiaweb' user='erik1' host='localhost' password='{db_pw}'")

# Sometimes a failed query results in "current transaction is aborted, commands ignored until end of transaction block"
# on a subsequent query. Set auto commit to get around this?
conn.set_session( autocommit=True)
cur = conn.cursor()

# Is no worky, apparently need to use RealDictCursor
# dcur = conn.cursor( cursor_factory = psycopg2.extras.DictCursor)
dict_cur = conn.cursor( cursor_factory = psycopg2.extras.RealDictCursor)


def prep_dbq_pydict( sql, data={} ):
	# wrapper around prep_dbq to create real actual python dicts from the sql output instead of lame manky RealDictRows
	dict_result = []
	result = prep_dbq( sql, data )
	
	if type( result) is list:
		for row in prep_dbq( sql, data ):
			dict_result.append(dict(row))
	elif type( result) is int:
		dict_result = result	
	else:
		pass
		# print('Not sure what to do with this DB query result:')
		# pprint( result)

	return dict_result

sa_sess = Session(engine)
sa_conn = engine.connect()

def prep_dbq_yield( sql, data={} ):
    # def prep_dbq_yield( table, where, data={} ):
	
    # for record in sa_sess.query( text( sql)).yield_per(10):
    result_proxy = sa_conn.execution_options(stream_results=True).execute( text(sql)).yield_per(10000)
    for record in result_proxy:
        # print(record)
        # print(record._asdict())
        yield record._asdict()
        # print(result_proxy.keys())
        # exit(8)

    return 0

    with engine.begin() as conn:
        qry = engine.text("SELECT FirstName, LastName FROM clients WHERE ID < 3")
        resultset = conn.execute(qry)
        results_as_dict = resultset.mappings().all()

    return 0

    pprint(results_as_dict)
	# Execute a prepared statement, you know for SUCUURITEE!
	# print ( data)
	# if debug:
	# 	log ("sql: " + sql, data)

    if len( data) > 0:
        dict_cur.execute( sql, data)
    else:
       dict_cur.execute( sql)
	#conn.commit()
	# print ( cur.rowcount)
	# print(cur.statusmessage)
	# print( dict_cur.statusmessage, dict_cur.rowcount)
    if dict_cur.statusmessage.startswith('DO'):
		# As result of a DO/BEGIN piece of code
		# DDL returns a rowcount of -1?
       return dict_cur.rowcount
    if dict_cur.statusmessage.startswith('DELETE'):
       return dict_cur.rowcount
    if dict_cur.statusmessage.startswith('INSERT'):
		# print (dict_cur.rowcount)
        try:
            anything_returned = dict_cur.fetchall()
        except:
            anything_returned = False
        if anything_returned:
            return anything_returned
        else:
            return dict_cur.rowcount
    if dict_cur.rowcount > 0:
        try:
            ret = dict_cur.fetchall()
        except:
            ret = dict_cur.rowcount
        # print( sql, ret)
        return ret
    return


def prep_dbq( sql, data={} ):
	# Execute a prepared statement, you know for SUCUURITEE!
	# print ( data)
	if debug:
		log ("sql: " + sql, data)

	if len( data) > 0:
		dict_cur.execute( sql, data)
	else:
		dict_cur.execute( sql)
	#conn.commit()
	# print ( cur.rowcount)
	# print(cur.statusmessage)
	# print( dict_cur.statusmessage, dict_cur.rowcount)
	if dict_cur.statusmessage.startswith('DO'):
		# As result of a DO/BEGIN piece of code
		# DDL returns a rowcount of -1?
		return dict_cur.rowcount
	if dict_cur.statusmessage.startswith('DELETE'):
		return dict_cur.rowcount
	if dict_cur.statusmessage.startswith('INSERT'):
		# print (dict_cur.rowcount)
		try:
			anything_returned = dict_cur.fetchall()
		except:
			anything_returned = False
		if anything_returned:
			return anything_returned
		else:
			return dict_cur.rowcount
	if dict_cur.rowcount > 0:
		try:
			ret = dict_cur.fetchall()
		except:
			ret = dict_cur.rowcount
		# print( sql, ret)
		return ret
	return


def postgres_upsert(table, conn, keys, data_iter):
	from sqlalchemy.dialects.postgresql import insert

	data = [dict(zip(keys, row)) for row in data_iter]

	insert_statement = insert(table.table).values(data)
	upsert_statement = insert_statement.on_conflict_do_update(
		constraint=f"{table.table.name}_pkey",
		set_={c.key: c for c in insert_statement.excluded},
	)
	conn.execute( upsert_statement)	

def pandas_append_to_table( pd, table='', verbose=False, max_failures=0, LittleBitVerbose=True, upsert=None, pkey=None):
	# TODO: speed this up somehow. Proposal:
	# Add max_insert_failure parameter, e.g. 5:
	# Inserts will be tried starting from the back and the front of the frame. If more than 5 failures are observed
	# then this will be abandoned. Other processes would have to work out any missing data but in 99.99% cases this is
	# what needs to be done.

	if pkey is not None:
		# Add primary key in case it's not there
		sql_add_pk = f"""
		ALTER TABLE IF EXISTS {table}
    ADD CONSTRAINT {table}_pkey PRIMARY KEY ({pkey})"""

		sql = f"""DO $$
BEGIN
  BEGIN
    {sql_add_pk};
  EXCEPTION
    WHEN duplicate_object THEN RAISE NOTICE 'Table constraint foo.bar already exists';
    WHEN OTHERS THEN RAISE NOTICE 'Sumthing else went wrong';
  END;
END $$;"""

		prep_dbq_pydict( sql)

	from sqlalchemy.exc import IntegrityError
	# Try to insert the lot first:
	try:
		if upsert is not None:
			# Try postgres UPSERT first but if more than 1000 do it piece wise
			# otherwise postgres memory usage spirals out of control for some reason
			step_size = 1000
			if len( pd) > step_size:
				for i in range( 0, len(pd) - 1, step_size):
					print( f'{i} ', end='')
					pd.iloc[i:i+step_size].to_sql( name=table, if_exists='append', con=engine, schema='public', index=False, method=postgres_upsert)
		else:
			pd.to_sql( name=table, if_exists='append', con=engine, schema='public', index=False, 
			chunksize=50000)
			# chunksize=50000, method="multi")
    	    #  chunksize=10000 )
			hm('done at once')
		# , method='multi'
		if verbose:
			print( f'Table {table} -  ' + str(len(pd)) + ' rows')

		if LittleBitVerbose:
			row_inserts = len( pd)
			msg = f"\tTable {table}: +{row_inserts} (all)"
			print( msg)

		return( row_inserts, 0)
	except IntegrityError as e:
		try:
			if upsert is not None:
				# Try postgres UPSERT first but if more than 1000 do it piece wise
				# otherwise postgres memory usage spirals out of control for some reason
				step_size = 1000
				if len( pd) > step_size:
					for i in range( 0, len(pd) - 1, step_size):
						print( f'{i} ', end='')
						pd.iloc[i:i+step_size].to_sql( name=table, if_exists='append', con=engine, schema='public', index=False, method=postgres_upsert)
						# row_inserts += len( pd.iloc[i:i+step_size])
				else:
					pd.to_sql( name=table, if_exists='append', con=engine, schema='public', index=False, method=postgres_upsert)

				if LittleBitVerbose:
					row_inserts = len( pd)
					msg = f"\tTable {table}: +{row_inserts} (all using UPSERT)"
					print( msg)
				return( row_inserts, 0)

		except IntegrityError as e:
			pass

	if verbose:
		print( f'Table {table} -  Could not insert entire frame, attempting row by row')			



	# Insert the data row by row and catch the error if the row already exists:
	row_inserts = 0
	rows_skipped = 0
	failures_front = 0
	failures_back = 0
	if max_failures > 0 and verbose:
		print("Attempting inserting from front of frame first:")

	pd_size = len( pd)
	# PDFs indexes start at 0 and end at len() - 1
	for i in range( 0, pd_size - 1):
		try:
			pd.iloc[i:i+1].to_sql( name=table, if_exists='append', con=engine, schema='public', index=False)
			if verbose:
				print( '+', end = '')
			row_inserts += 1
		except IntegrityError as e:
			if verbose:
				print( '_', end = '')
			rows_skipped += 1
			if max_failures > 0 and rows_skipped >= max_failures:
				if verbose:
					print(f" Amount of max failures ({max_failures}) reached. Attempting inserting from back of the frame...")
				break
			pass #or any other action

	for i in range( pd_size - 1, max_failures - 1, -1):
		try:
			pd.iloc[i:i+1].to_sql( name=table, if_exists='append', con=engine, schema='public', index=False)
			if verbose:
				print( '+', end = '')
			row_inserts += 1
		except IntegrityError as e:
			if verbose:
				print( '_', end = '')
			rows_skipped += 1
			if max_failures > 0 and rows_skipped >= max_failures * 2:
				if verbose:
					print(f" Amount of max failures ({max_failures}) reached. Skipping middle rows of frame entirely.")
				break
			pass #or any other action
	if verbose:
		print('\nTable ''{}'' -  Rows inserted={} skipped={}'.format( table, row_inserts, rows_skipped))

	if LittleBitVerbose:
		msg = f"\tTable {table}: o {rows_skipped}"
		if row_inserts > 0:
			msg += f", + {row_inserts}"
		msg += f" (of {pd_size})"
		print( msg)

	return( row_inserts, rows_skipped)

def hm( msg, pre = '*'):
    # Hacker message, what else ;)
    CYAN = '\033[96m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    RED = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'
    if pre == '!': msg = f"{RED}[{pre}] {msg}"
    elif pre == '+': msg = f"{GREEN}[{pre}] {msg}"
    elif pre == '-': msg = f"{YELLOW}[{pre}] {msg}"
    else: msg = f"{CYAN}[{pre}] {msg}"
    print( f"{BOLD}{msg}{ENDC}")


def preview_array( arr):
    l = len( arr)
    hm( f'Array size: {l:,} , lows and highs:')
    # pprint( arr)
    if isinstance(arr, dict):
        for k, v in arr[:15]:
            hm( f"{k}, {v:,.3f}", '-')
        print('...')
        for k, v in arr[-15:]:
            hm( f"{k}, {v:,.3f}", '+')
    else:
        for v in arr[:15]:
            if v is float:
                hm( f"{v:,.3f}", '-')
            else:
                hm( f"{v}", '-')
        print('...')
        for v in arr[-15:]:
            if v is float:
                hm( f"{v:,.3f}", '+')
            else:
                hm( f"{v}", '+')


def check_before_write( filename, data, feedback = 'none'):
	# SSD optimization. Read the file as a string and don't
	# rewrite it unless the data has changed.

    if os.path.isfile( filename):
        with open(filename, 'r') as myfile:
            existingdata = myfile.read()
        if existingdata == data:
            if feedback == 'char':
                print('_', end='')
            # print ( '=> ' + filename + ' : Already detected identical contents. File not rewritten.')
            return True
    # In any other case we need to rewrite the data:
    fh = open( filename, "w")
    fh.write( data)
    if feedback == 'char':
        print('+', end='')
    fh.close()
    # print ( '=> {:s} : {:s} bytes written.'.format( filename, str(len(data))))

def df_write_js_array( js_file, js_array_prefix, df, fields):

    # Split the df in 100 parts and write them to the set directory accordingly
    pd.set_option( 'display.max_columns',  1000)
    pd.set_option( 'display.width',       32000)
    pd.set_option( 'display.float_format', '{:.1f}'.format)
    np.set_printoptions(threshold=np.inf)
    np.set_printoptions(suppress=True)
    # not working or only if lines become too long, not for joining them together?
    np.set_printoptions( linewidth = 120)

    # size = len( df)
    # for element_idx in range( 0, 100):
    #     start = int(element_idx / 100 * size)
    #     stop = int((element_idx + 1) / 100 * size) - 1
        # print( 'stop/start: ', start, stop)
        # print( df.iloc[start:stop+1])
        # Is that some old style string formatting??
    # print( df[ fields])
    print( df[ fields].values)
    # js_array = str( df[ fields].values.tolist())
    # np.list2
    # js_array = np.array2string( np.asarray( df[ fields].values.tolist())
    # fmt = {
	#         'float_kind': lambda x: "%d" % x if round(x) == x else "%.1f" % x,
	#         'complex_kind': lambda x: "%d" % x if round(x) == x else "%.1f" % x
	#     }
    
    fmt = {
	        'float_kind': lambda x: "%.1f" % x,
	        'complex_kind': lambda x: "%.1f" % x,
		    'object': lambda x: "%.1f" %x if isinstance( x, float) else "\"%s\"" % x
	    }
    
    js_array = np.array2string( df[ fields].to_numpy()
        , precision=4, separator=',' ,suppress_small=True
        , formatter= fmt
        , max_line_width=120
	    # ,floatmode = 'fixed'
	)
    # js_array = df[ fields].to_string(
	#     col_space=0,
	#     index=False,
	#     justify='unset'


    # )
    # , precision=4, separator=',' ,suppress_small=True
    # , formatter= fmt
    # , max_line_width=120
    # ,floatmode = 'fixed'
	# )
    # print( js_array[:1000])
    # exit(8)
    
    # js_file = f'{SET_JS_BASEPATH}{set_name}/{element_idx}.js'
    check_before_write( js_file, js_array_prefix + js_array, feedback='char')
    print('')


def df_write_gaia_set( set_name, js_array_prefix, df, fields):

    # Split the df in 100 parts and write them to the set directory accordingly
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
        js_array = np.array2string( df[ fields].iloc[start:stop+1].values
            , precision=3, separator=',' ,suppress_small=True
            , formatter={'float_kind':lambda x: "%d" % x if round(x) == x else "%.1f" % x }
            , max_line_width=120)
        # print( js_array)
        
        js_file = f'{SET_JS_BASEPATH}{set_name}/{element_idx}.js'
        check_before_write( js_file, js_array_prefix + js_array, feedback='char')
        print('')

def get_pg_count_star( table_name, where_clause=''):
    rows = prep_dbq_pydict( f"select count(*) from {table_name} {where_clause}")
    # cur.execute( f"select count(*) from {table_name} {where_clause}")
    # rows = cur.fetchall()
    # print(rows)
    # exit(8)
    count = rows[0]['count']
    return count

def ra_text_to_deg( ra_txt):
    ra = 0
    ra_m1 = re.match( r'(\d+)\^h\s+([\d\.]+)\^m', ra_txt )
    if ra_m1:
        # print( ra_m1.group(1))
        # print( ra_m1.group(2))
        ra += float( ra_m1.group(1)) * 15
        ra += float( ra_m1.group(2)) * 15/60
    # print(ra)
    return ra

def dec_text_to_deg( dec_txt):
    dec = 0
    dec_m1 = re.match( r'^([^\d])+(\d+)°\s+([\d\.]+)[′]', dec_txt )
    if dec_m1:
        dec += float( dec_m1.group(2))
        dec += float( dec_m1.group(3)) / 60
        if dec_m1.group(1) in ['-','−']:
            dec = -dec
    return dec

def pandas_calc_xyz( df):
	# This assumes df has columns ra, dec and dist in deg, deg and ly respectively
    df['x'] = np.cos( df['ra'] * DEG2RAD) * np.cos( df['dec'] * DEG2RAD) * df['dist']
    # print("[+] Calculating y's ...")
    df['y'] = np.sin( df['ra'] * DEG2RAD) * np.cos( df['dec'] * DEG2RAD) * df['dist']
    # print("[+] Calculating z's ...")
    df['z'] = np.sin( df['dec'] * DEG2RAD) * df['dist']
    return df
 


suitable_parameters_from_stats = [
    {'px_over_err': 20, 'dist': 5000, 'abs_mag': 15, 'mil_stars' : 41 },
    {'px_over_err': 20, 'dist': 10000, 'abs_mag': 15, 'mil_stars': 48 },
    {'px_over_err': 30, 'dist': 5000, 'abs_mag': 15, 'mil_stars': 28 },
    {'px_over_err': 40, 'dist': 3000, 'abs_mag': 15, 'mil_stars': 16 },
     {'px_over_err': 80, 'dist': 2000, 'abs_mag': 15, 'mil_stars': 6.3 },
     {'px_over_err': 50, 'dist': 2000, 'abs_mag': 10, 'mil_stars': 8.9 },
    {'px_over_err': 20, 'dist': 3000, 'abs_mag': -1, 'mil_stars': 6.0 },
     {'px_over_err': 50, 'dist': 4000, 'abs_mag': -1, 'mil_stars': 7.4 },
     {'px_over_err': 50, 'dist': 5000, 'abs_mag': -2, 'mil_stars': 4.2 },
     {'px_over_err': 40, 'dist': 5000, 'abs_mag': -2, 'mil_stars': 5.4 },
    {'px_over_err': 30, 'dist': 5000, 'abs_mag': -2, 'mil_stars': 6.5 },
    {'px_over_err': 20, 'dist': 10000, 'abs_mag': -3, 'mil_stars': 6.3 },
    {'px_over_err': 10, 'dist': 20000, 'abs_mag': -3, 'mil_stars': 4.5 },
]
GAIAWEB_DATA_SETS = {
    # 'px5-3000ly': "WHERE parallax / parallax_error > 5 and sqrt(x*x + y*y + z*z) < 3000",
    # 'px130-3000ly': "WHERE px_over_err > 130 and dist < 3000",
    # 'px100-2500ly': "WHERE px_over_err > 100 and dist < 2500",
    # 'px100-2500ly': "WHERE px_over_err > 100 and dist < 2500 and abs_mag < 6",
    # 'px5-500ly':    "WHERE px_over_err > 5 and dist < 500",
    # 'px10-1000ly':  "WHERE px_over_err > 10 and dist < 1000",
    # 'px10-5000ly-mag-0': "WHERE px_over_err > 10 and dist < 5000  and abs_mag < 0",
    # 'px50-all-mag--5': "WHERE px_over_err > 50 and abs_mag < -5",
    # 'px40-all-mag--3': "WHERE px_over_err > 40 and abs_mag < -3",
}

for params in suitable_parameters_from_stats:
     name = f'px{params["px_over_err"]}_{params["dist"]}ly_{params["abs_mag"]}mag'
     sql_where = f'''
     WHERE px_over_err > {params["px_over_err"]} 
        and dist < {params["dist"]} 
        and abs_mag < {params["abs_mag"]}'''
     GAIAWEB_DATA_SETS[name] = sql_where

# pprint(GAIAWEB_DATA_SETS)
# exit(9)


# Should support overlap between bins or not?
GAIAWEB_BIN_SETS = {
    # 'px5-3000ly': "WHERE parallax / parallax_error > 5 and sqrt(x*x + y*y + z*z) < 3000",
    'star-density-px5-10kly-p100ly': {
        'where': '''
        WHERE FALSE  
        or ((dist < 10000) and (px_over_err > 5))
        ''',
        'bin_base_cols': [ 'x', 'y', 'z'],
        'step_size': 100,
        # 'analyse':
        'what': 'count',
        'what_field': 'count', # For 'count' this field will be created
        'cut_below': 0.05,
        'color_scale': [ (1,0,0), (0,0,1)],
    },
    'star-density-px-10-all-p10ly-mag0': {
        'where': '''
        WHERE FALSE  
        or ((px_over_err > 10) and (abs_mag < 0))
        ''',
        'bin_base_cols': [ 'x', 'y', 'z'],
        'step_size': 10,
        # 'analyse':
        'what': 'count',
        'what_field': 'count', # For 'count' this field will be created
        'cut_below': 0.05,
        'color_scale': [ (1,0,0), (0,0,1)],
    },
    'star-density-px-10-p500ly-all': {
        'where': '''
        WHERE FALSE  
        or (px_over_err > 10)
        ''',
        'bin_base_cols': [ 'x', 'y', 'z'],
        'step_size': 500,
        # 'analyse':
        'what': 'count',
        'what_field': 'count', # For 'count' this field will be created
        'cut_below': 0.05,
        'color_scale': [ (1,0,0), (0,0,1)],
    },
    'avg-star-mag-px5-10kly-p100ly': {
        'where': '''
        WHERE FALSE  
        or (dist < 10000) and (px_over_err > 5)
        ''',
        'bin_base_cols': [ 'x', 'y', 'z'],
        'step_size': 100,
        # 'analyse':
        'what': 'avg',
        'what_field': 'abs_mag',  # This is an existing field that will be averaged and stored with the same name
        'color_scale': [ (1,0,0), (0,0,1)],
    },
    'avg-color-10kly-p100ly': {
        'where': '''
        WHERE FALSE  
        or (dist < 10000) and (px_over_err > 5)
        ''',
        'bin_base_cols': [ 'x', 'y', 'z'],
        'step_size': 100,
        # 'analyse':
        'what': 'avg',
        'what_field': 'color',  # This is an existing field that will be averaged and stored with the same name
        'color_scale': [ (1,0,0), (0,0,1)],
    },
    # 'avg_star_mag': {
    #     'where': '''
    #     WHERE FALSE  
    #     or (dist < 500)
    #     ''',
    #     'bin_base_cols': [ 'x', 'y', 'z'],
    #     'step_size': 100,
    #     # 'analyse':
    #     'what': 'avg',
    #     'what_field': 'abs_mag',  # This is an existing field that will be averaged and stored with the same name
        
    # },
    
    #'px50-all': "WHERE px_over_err > 50"
}


SELECT_ROUNDED_SQLITE_CLAUSE='''
printf("%.1f", x) as x,
printf("%.1f", y) as y,
printf("%.1f", z) as z,
printf("%.1f", color) as color,
printf("%.1f", abs_mag) as abs_mag,
dist

'''

SELECT_ROUNDED_PG_CLAUSE='''
round( x::numeric, 1) as x,
round( y::numeric, 1) as y,
round( z::numeric, 1) as z,
round( color::numeric, 1) as color,
round( abs_mag::numeric) as abs_mag,
dist
'''
