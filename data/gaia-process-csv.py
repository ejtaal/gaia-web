#!/usr/bin/env python3

# Requirements:
# Pandas

# from quantics_include import *

import argparse
# import copy
import os
from io import StringIO

# from random import random, randint
	
parser = argparse.ArgumentParser(description='Process GAIA DR3 gzipped datafiles.')

parser.add_argument('FILE', nargs=1, type=str, help='file to process, e.g. gaia_source001.csv.gz')
# parser.add_argument('more', metavar='MORE', nargs='*', help='More details')

args = parser.parse_args()

# print( args)
# print( args.FILE)

import pandas as pd
import gzip
from alive_progress import * 


columns_to_keep = [
'source_id',
'ra',
'ra_error',
'dec',
'dec_error',
'parallax',
'parallax_error',
'parallax_over_error',
'pmra',
'pmra_error',
'pmdec',
'pmdec_error',
'nu_eff_used_in_astrometry',
'pseudocolour',
'teff_gspphot',
'radial_velocity',
'radial_velocity_error',
'phot_g_mean_mag'
]
# 'designation',
# 'random_index',

csvstring = ''
lines = []
header_seen = False
csv_file = args.FILE[0]
sqlite_db = csv_file.replace( '.csv.gz', '') + '.sqlite'
jsfile_out = csv_file.replace( '.csv.gz', '') + '.js'

print("[+] Unzipping file & stripping comments ...")
with gzip.open( csv_file, mode="rt") as f:
    for line in alive_it( f):
        if line.startswith('#'):
            continue
        if line.startswith('solution_id'):
            if header_seen:
                continue
            header_seen = True
        # print('got line', line)
        # csvstring += line
        lines.append( line)
    # file_content = f.read()

# print( csvstring)
# print( lines[:5])
# print( ''.join(lines[:5]))

# exit(0)
# csvStringIO = StringIO( csvstring)
# csvStringIO = StringIO( '\n'.join( lines))
csvString = ''.join( lines)
print( 'lines read: ', len( lines))
# print( 'len csvString: ', len( csvString))

print("[+] Generating StringIO object from lines read ...")
csvStringIO = StringIO( csvString)
# csvStringIO = StringIO( lines)

print("[+] Converting csvstring into Pandas dataframe ...")
all_stars = pd.read_csv( csvStringIO, sep=",", usecols=columns_to_keep )

# filtered_stars = df[ (df['parallax'] > 0) & (df['parallax_over_error'] < 1)]
# filtered_stars = all_stars[ ( all_stars['parallax'] > 0)]

print( all_stars)
# TODO, find best value for cut off
# filtered_stars = all_stars[ ( all_stars['parallax'] > 0.001)]
# filtered_stars = all_stars[ ( all_stars['parallax_over_error'] > 1)]
# df = all_stars[ ( all_stars['parallax_over_error'] > 1)].copy()
df = all_stars[ ( all_stars['parallax_over_error'] > 0.5) & ( all_stars['parallax'] > 0.001)].copy()

import numpy as np

DEG2RAD = np.pi / 180;
lightyear_p_parsec = 3.261563777
# var wstream = fs.createWriteStream('stars.bin');
# db.each(`SELECT ${fields.join(',')} from stars where parallax > 0`, function(err, row) {
# df = filtered_stars
print("[+] Calculating distances in lightyears ...")
df['dist'] = lightyear_p_parsec * 1 / (df['parallax'] * 0.001)
print("[+] Calculating x's ...")
df['x'] = np.cos( df['ra'] * DEG2RAD) * np.cos( df['dec'] * DEG2RAD) * df['dist']
print("[+] Calculating y's ...")
df['y'] = np.sin( df['ra'] * DEG2RAD) * np.cos( df['dec'] * DEG2RAD) * df['dist']
print("[+] Calculating z's ...")
df['z'] = np.sin( df['dec'] * DEG2RAD) * df['dist']
print("[+] Determining colors ...")
df['color'] = df['nu_eff_used_in_astrometry']
df.color.fillna( df.pseudocolour, inplace=True)
df.color.fillna( 0, inplace=True)
df['phot_g_mean_mag'].fillna( 10, inplace=True)
df['abs_magnitude'] = df['phot_g_mean_mag'] + 5 - 5 * np.log10( df['dist'] * lightyear_p_parsec)
# TODO: calc absolute magnitude

filtered_stars = df
save_db_stars = filtered_stars[ ['parallax', 'parallax_error', 'x', 'y','z', 'color', 'abs_magnitude']]
# print( filtered_stars)
print( save_db_stars)


# print( f"[+] Writing filtered stars to {sqlite_db} ...")
# import sqlite3
# conn = sqlite3.connect( sqlite_db)
# save_db_stars.to_sql( 'gaia_source_filtered', conn, if_exists='replace', index=False)

# exit(0)

# stars_xyz_list = filtered_stars[ ['x','y','z']].itertuples(index=False, name=None)
# records is the fastest way to extract a list of tuples

# filtered_stars = df[ df['dist'] < 500 ]
nearby_stars = df[ df['dist'] < 500 ]
nearish_stars = df[ df['dist'] < 5000 ]
galactic_stars = df[ (df['dist'] > 2000) & (df['dist'] < 50000) ]
filtered_stars = nearish_stars
print( filtered_stars)
print( filtered_stars[ ['ra', 'dec', 'parallax', 'parallax_error', 'parallax_over_error', 
        'pseudocolour', 'abs_magnitude', 'color', 'dist', 'x', 'y','z']])

stars_xyz_list = filtered_stars[ [ 'x','y','z','color','abs_magnitude']].to_records(index=False).tolist()
# stars_xyz_list = near_stars[ [ 'x','y','z','color']].to_records(index=False).tolist()

# stars_colors_list = len( stars_xyz_list) * [[ 1, 1, 1]]

# print( list( stars_xyz_list))

jsfile_contents = "\nvar stars = " + str( stars_xyz_list) + ";\n"
# jsfile_contents += "\nvar star_colors = " + str( stars_colors_list) + ";\n"
# jsfile_contents += "\nvar star_max_dist = " + str( max( filtered_stars['dist'])) + ";\n"

jsfile_contents = jsfile_contents.replace('(','[').replace(')',']').replace('], ', "],\n\t")

import re
jsfile_contents = re.sub( r'(\d\.\d{3})\d+', r'\1', jsfile_contents)

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
        
def write_file( filename, contents):
    check_before_write( filename, contents)
    # handle = open( filename, 'w')
    # handle.write( contents)
    # handle.close()

# jsfile_out = 'stars-test-01.js'

print( f"[+] Writing jsfile to {jsfile_out} ...")
write_file( jsfile_out, jsfile_contents)

# print( jsfile_contents)

exit(0)

# print( stars_xyz_list[:10])




# csvfile_handle
# csvfile_handle = open( args.FILE, 'r')
# wordlist_lines = []
# # wordlist_lines = wordlist_handle.readlines()
# # wordlist_linecount = 0

# count = 0
# while True:
#     count += 1
#     # Get next line from file
#     line = csvfile_handle.readline()
  
#     # if line is empty
#     # end of file is reached
#     if not line:
#         break
#     # print("Line{}: {}".format(count, line.strip()))
    
#     # # Add capitalized and non capitalized to the list
#     # # TODO: Make this configurable as it increases the passphrase keyspace by 2^n for n words/columns used.
#     # print("Line{}: {}".format(count, line.strip().capitalize()))
#     # print("Line{}: {}".format(count, line.strip().lower()))
#     wordlist_lines.append( line.strip().capitalize())
#     wordlist_lines.append( line.strip().lower())
#     if line.strip().lower() != line.strip():
#         # Add original too in case it has some capitalization in the middle somewhere?
#         wordlist_lines.append( line.strip())





# csvString = 'test'
# csvStringIO = StringIO(csvString)

# df = pd.read_csv( csvStringIO, sep=",", header=None)

# pd.DataFrame( pd.read_csv( './mychanges.csv.bak', delimiter=',', na_values=['null']))