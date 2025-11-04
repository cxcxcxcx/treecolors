tippecanoe --force -o trees.mbtiles -zg --drop-densest-as-needed -l trees \
 trees_palo_alto.geojson \
 trees_san_jose.geojson \
 trees_cupertino.geojson \
 trees_sf.geojson
pmtiles convert trees.mbtiles web/trees.pmtiles
