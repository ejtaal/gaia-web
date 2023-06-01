

Columns to include for which purpose:

# Ultimate goals:

- 3D star field featuring:
  - as many stars as possible
    - if not, then the nearest/furthest to try and get outline of local galaxy
  - approx colors
  - approx size 1-4 px as per absolute magnitude
  - mark stars known with exoplanets
  - display arrows as per calculated 3d motion vector
  - allow warp-like zooming/moving
  - allow sharing of location+view angle to pinpoint interesting galactic locations such as star clusters etc.
- 3D galaxy field
  - Galaxy candidates - redshifts 	1,367,153

- GUI requirements
  - toggle between Sol-centered viewing and Star Trek fly through mode (plus warp engage mode of course)
  - toggle between only rendering between Sol and point of camera or everything
  - determine max Cloudflare size caching for max file sizes ( 512 MB/  https://developers.cloudflare.com/cache/about/default-cache-behavior/) with correct headers and file extensions

# Columns we need to star field features

https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html



- designation : Unique source designation (unique across all Data Releases) (string)
- source_id : Unique source identifier (unique within a particular Data Release) (long)
- random_index : Random index for use when selecting subsets (long)
- ra : Right ascension (double, Angle[deg])
- ra_error : Standard error of right ascension (float, Angle[mas])
- dec : Declination (double, Angle[deg])
- dec_error : Standard error of declination (float, Angle[mas])
- parallax : Parallax (double, Angle[mas] )
- parallax_error : Standard error of parallax (float, Angle[mas] )
- parallax_over_error : Parallax divided by its standard error (float)
- pmra : Proper motion in right ascension direction (double, Angular Velocity[mas yr−1])
- pmdec : Proper motion in declination direction (double, Angular Velocity[mas yr−1] )
- pmdec_error : Standard error of proper motion in declination direction (float, Angular Velocity[mas yr−1] )
- pseudocolour : Astrometrically estimated pseudocolour of the source (float, Misc[μm−1])
- radial_velocity : Radial velocity (float, Velocity[km s−1] )
- radial_velocity_error : Radial velocity error (float, Velocity[km s−1] )
- phot_g_mean_mag : G-band mean magnitude (float, Magnitude[mag])

<!-- Instead of calculating our own Sol based x/y/z coordinates, galactic coordinates may be used instead ( https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu3ast/sec_cu3ast_intro/ssec_cu3ast_intro_tansforms.html#SSS1 using formula 4.59: 
rGal = [XGal, YGal, ZGal] = [coslcosb, sinlcosb, sinb].
). These columns will be needed:
- l : Galactic longitude (double, Angle[deg])
- b : Galactic latitude (double, Angle[deg])
- (which column determines length of vector though?) -->

select round( abs_mag) abs_mag_rounded, round( avg( dist)) as avg_distance, count(*) from grand_gaia_source 
group by abs_mag_rounded

"abs_mag_rounded"	"avg_distance"	"count"
-14	15129	2
-13	13043	73
-12	12232	261
-11	12790	1010
-10	19016	10185
-9	19991	123212
-8	19009	483711
-7	16854	1113339
-6	14648	2728476
-5	11849	5847514
-4	10281	5912346
-3	8278	12527877
-2	6949	29424681
-1	5782	37002128
-0	4614	31867721
 1	3569	21909892
 2	2668	14893745
 3	1973	11295516
 4	1495	8288227
 5	1148	4557908
 6	868	2177088
 7	652	1077939
 8	492	587870
 9	372	271076
10	280	85792
11	203	18563
12	140	2454
13	87	218
14	51	20
15	32	4


# SIMBAD query to get NAME - HIP - DR3 references

-- Find all objects that have both a NAME as well as either a HIP or Gaia DR3 reference
SELECT 
-- id1.id, ids.ids
ID1.OIDREF, ID1.ID
-- count(ID1.OIDREF)
--count(*)
FROM 
ident AS id1 
JOIN ids as ids USING(oidref)
WHERE
-- WHERE id1.id = 'tet01 Ori C' AND
(
    id1.id LIKE 'NAME %'
  OR id1.id LIKE 'HIP %'
  OR id1.id LIKE 'Gaia DR3 %'
)
AND
(
    ids.ids LIKE '%|NAME%'
  OR ids.ids LIKE 'NAME%')
AND 
((
  ids.ids LIKE '%|Gaia DR3%'
  OR ids.ids LIKE 'Gaia DR3%'
 )
     OR
(
  ids.ids LIKE '%|HIP %'
  OR ids.ids LIKE 'HIP %'
 )
)
;

# The Fifth Catalogue of Nearby Stars (CNS5) - 

https://dc.zah.uni-heidelberg.de/tableinfo/cns5.main

Column info:

g_mag 	G 	G band mean magnitude (corrected) 	mag 	phot.mag;em.opt

parallax 	ϖ 	Absolute trigonometric parallax 	mas 	pos.parallax.trig
parallax_error 	Err. ϖ 	Error in parallax 	mas 	stat.error;pos.parallax.trig

# HIP data

Original: https://cdsarc.cds.unistra.fr/viz-bin/nph-Cat/txt.gz?I/239/hip_main.dat

Revised: https://www.gaia.ac.uk/science/parallax/hipparcos-new-reduction

