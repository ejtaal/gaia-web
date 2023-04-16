from pprint import pprint
import os


SOURCE_DB_PATH = "./source"
SET_JS_BASEPATH = "./set-"
GRAND_DB_FULLPATH = "./grand/Grand_gaia_source.sqlite"
GRAND_DB_TABLENAME = 'grand_gaia_source'

BIN_DB_BASEPATH = "./bins/"



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
			print ( '=> ' + filename + ' : Already detected identical contents. File not rewritten.')
			return True
	# In any other case we need to rewrite the data:
	fh = open( filename, "w")
	fh.write( data)
	fh.close()
	print ( '=> {:s} : {:s} bytes written.'.format( filename, str(len(data))))


GAIAWEB_DATA_SETS = {
    # 'px5-3000ly': "WHERE parallax / parallax_error > 5 and sqrt(x*x + y*y + z*z) < 3000",
    'px5-3000ly': "WHERE px_over_err > 5 and dist < 3000",
    'px50-all': "WHERE px_over_err > 50"
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
printf("%.1f", x),
printf("%.1f", y),
printf("%.1f", z),
printf("%.1f", color),
printf("%.1f", abs_mag)
'''