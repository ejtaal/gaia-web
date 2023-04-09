

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


