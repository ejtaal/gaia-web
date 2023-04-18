
import pandas as pd
import numpy as np
from pprint import pprint
import os


SOURCE_DB_PATH = "./source"
SET_JS_BASEPATH = "./set-"
GRAND_DB_FULLPATH = "./grand/Grand_gaia_source.sqlite"
GRAND_DB_TABLENAME = 'grand_gaia_source'

BIN_DB_BASEPATH = "./bins/"

GAIA_WEB_DATA_SET_INDEX = "./gaia-web-data-sets-index.js"



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


def check_before_write( filename, data):
	# SSD optimization. Read the file as a string and don't
	# rewrite it unless the data has changed.

	if os.path.isfile( filename):
		with open(filename, 'r') as myfile:
			existingdata = myfile.read()
		if existingdata == data:
			# print ( '=> ' + filename + ' : Already detected identical contents. File not rewritten.')
			return True
	# In any other case we need to rewrite the data:
	fh = open( filename, "w")
	fh.write( data)
	fh.close()
	# print ( '=> {:s} : {:s} bytes written.'.format( filename, str(len(data))))


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
            , formatter={'float_kind':lambda x: "%d" % x if round(x) == x else "%.3f" % x }
            , max_line_width=120)
        # print( js_array)
        
        js_file = f'{SET_JS_BASEPATH}{set_name}/{element_idx}.js'
        check_before_write( js_file, js_array_prefix + js_array)










GAIAWEB_DATA_SETS = {
    # 'px5-3000ly': "WHERE parallax / parallax_error > 5 and sqrt(x*x + y*y + z*z) < 3000",
    'px150-3000ly': "WHERE px_over_err > 150 and dist < 3000",
    'px5-500ly': "WHERE px_over_err > 5 and dist < 500",
    'px10-1000ly': "WHERE px_over_err > 10 and dist < 1000",
    'px5-3000ly': "WHERE px_over_err > 10 and dist < 3000",
    'px50-all-mag0': "WHERE px_over_err > 50 and abs_mag < 0"
}


GAIAWEB_BIN_SETS = {
    # 'px5-3000ly': "WHERE parallax / parallax_error > 5 and sqrt(x*x + y*y + z*z) < 3000",
    'star_density': {
        'where': '''
        WHERE FALSE  
        or (dist < 10000)
        and (px_over_err > 5)
        ''',
        'bin_base_cols': [ 'x', 'y', 'z'],
        'step_size': 100,
        # 'analyse':
        'what': 'count',
        'what_field': 'count', # For 'count' this field will be created
        'cut_below': 0.05

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


SELECT_ROUNDED_CLAUSE='''
printf("%.1f", x) as x,
printf("%.1f", y) as y,
printf("%.1f", z) as z,
printf("%.1f", color) as color,
printf("%.1f", abs_mag) as abs_mag,
dist

'''

# printf("%.1f", abs_mag) as 
