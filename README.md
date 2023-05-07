# About

This repo contains Scripts to process GAIA DR3+ data and convert it into a Three.js visualization for the web, allowing one to either fly through the star using WASD and mouse movement, or visit interesting spots in the galactic neighbourhood via the built-in tour facility.

# Live demo

https://ejtaal.github.io/gaia-web/gaia-web-starfield.html

The demo is courtesy of Github Pages and currently hosts these datasets through the gaia-web-data repository:
- 'wp-open-clusters-150ly' (~290 MB, this only contains the data surrounding points of interest) 
- 'px80_2000ly_15mag' (~175 MB, px over error > 80, up to 2000ly away and up to absolute magnitude 15, i.e. all stars)
- 'px50_4000ly_-1mag' (~220MB)
- 'px20_10000ly_-3mag' (~200MB)
- 'px20_10000ly_15mag' (~1.4GB)

Please note that with standard webserver gzip compression, actual data transferred is around 30-40% of the numbers above.

# Running it locally

To avoid downloading all this data over the internet and host it locally instead, create an empty folder on your machine, then clone the gaia-web and gaia-web-data repositories both in there. Then run a http server from the folder, e.g.:

```
$ mkdir gaia && cd gaia
$ git clone https://github.com/ejtaal/gaia-web
$ git clone https://github.com/ejtaal/gaia-web-data
$ python3 -m http.server --directory . 8082
```

You should then be able to see the website at:
http://127.0.0.1:8082/gaia-web/gaia-web-starfield.html


A word only conveys a milli-picture, so here is a screenshot of work in progress, showing a side view of the Hyades cluster with Sol at the axes origin:

![Gaia Web @ Hyades open cluster](GAIA-Web_3D_Starfield_v0.2.png)

A video can be found here:

[![IMAGE_ALT](https://img.youtube.com/vi/yiTVA2BYB5I/0.jpg)](https://www.youtube.com/watch?v=yiTVA2BYB5I)

The video shows off the "tour" feature, where the camera visits some open clusters and flys around them. (Yes, annotations and smoother orbits are already on TODO list ;) )

The orange stripes are there because at the time of creating the video I only had about 10% of all Gaia data files, chosen at random. Because the Milky Way is overrepresented according to the HEALPix division of the data (See https://www.cosmos.esa.int/web/gaia-users/archive/extract-data and this lovely picture: https://www.cosmos.esa.int/documents/3414525/8760265/GaiaDR3_partitions_galactic.png/a2852722-bd04-d86c-ffc4-ed877b22fc93?t=1667563775853), this will result in "streams" of stars appearing to eminate from the origin/Sol as long as a full data
download hasn't been done yet.

One could say a picture only conveys a mill-VR scene, so hopefully I can host a semi-finished version somewhere that can handle some data usage.

# Why

Ever since learning about the Gaia mission I knew that, besides the obviously real science grown-ups would use it for, a visualization like this one would also be an amazingly awesome use of the data. Instead of watching the USS Enterprise flying through randomly generated star fields, one could explore our galaxy the way it actually is. I was hoping to one day create this project, but was intimidated by the learning curve of all 3D software. When I recently used Three.js for a work project which also featured a 3D scatter plot, it was much less painful than I imagined and hence applied the knowledge learned there to this project.

# Some tech details

Tech details of how data is extracted/stored/processed:
- csv files are downloaded from ESA's server
- stars with suitable parallax values are stored locally in sqlite
- all sqlite data is then stored in a large Postgres table with indexes on suitable columns to allow various data exports.
- data exports are prepared as JS arrays and split over 100 files each.
- only those with high confidence parallax are stored in a .js
- the starfield html page loads all .js files
- star data is loaded, black body colour is calculated according to stated temperatures and size according to absolute magnitude
- ...

# TODO:

- Process complete data set and split in interesting sections, e.g.:
  - Galactic outline (if descernable)
  - Local neighbourhood only
  - Search data for clusters by calculating star densities
- Datasets:
  - Add nebulae / dust clouds based on suitable astro photographs (could use help from a GSLS expert on how to efficiently create volumetric clouds as this seems to be a highly tricky thing to make)
  - focus on high density anomolies (globular/open clusters/nebulae), so this will rely on prior appropriate binning and using that to generate only star data for high density regions found.
  - Import 
- Annotate interesting features, e.g.:
  - Open clusters
  - Globular clusters (if present in data?)
  - Famous constellations / star systems (binaries etc)
  - known exoplanet hosts
  - Use Gaia Sky data for annotations?
  - Make stars glow (i.e. use GSLS trickery to create light sources instead of a sprite)
  - Implement waypoint tour
    - Done, but need some way of interacting with it / sharing / adding items / tagging tour stops etc...
    - Create open cluster waypoint tour dataset, where stretched out clusters have been contracted according to their highly unlike stretched out coordinates based on DR3 data alone, a contraction in the distance dimension only so to speak
  - Add hud view for camera viewing angle (done) and speed vector (speed still missing)
  - some sort of galactic or RA/dec minimap HUD view? Or grid on sky background option?
  - Done: Better tour navigation, i.e. next/prev/reset buttons at least
- Allow sharing of location / camera angle via url, e.g. http://site/gwsf#12,45,56@0.5,0.5,0.5 (would need to include selected dataset)
- Separate viewer and dataset for Gaia galactic candidates data set, using red-shift to calculate 3D position. Other datasets may have additional/more/better data too (SLOAN?).

# Credits

Inspiration was gained from the awesome pioneering work done by @flimshaw who used the 2016 Gaia DR1 data to construct a 3D visualization of it:
- Explanation: https://medium.com/@flimshaw/torrenting-the-galaxy-extracting-2-million-3d-stars-from-180gb-of-csvs-457ff70c0f93#.7g0zpkwnk
- The actual 3D demo: https://charliehoey.com/threejs-demos/gaia_dr1.html

# Other visualizations

- Gaia Sky (also awesome!): https://zah.uni-heidelberg.de/gaia/outreach/gaiasky
- Gaia's own visualization page: https://gea.esac.esa.int/archive/visualization/
