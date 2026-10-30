tippecanoe --force -o data/output/trees.mbtiles -zg --drop-densest-as-needed -l trees \
 data/output/geojson/trees_palo_alto.geojson \
 data/output/geojson/trees_san_jose.geojson \
 data/output/geojson/trees_cupertino.geojson \
 data/output/geojson/trees_sf.geojson \
 data/output/geojson/trees_berkeley.geojson \
 data/output/geojson/trees_fremontca.geojson \
 data/output/geojson/trees_sanleandroca.geojson \
 data/output/geojson/trees_sdtt.geojson \
 data/output/geojson/trees_los_angeles.geojson \
 data/output/geojson/trees_vancouver.geojson \
 data/output/geojson/trees_concordca.geojson
#  data/output/geojson/trees_oakland.geojson (bad lat lng)
pmtiles convert data/output/trees.mbtiles web/trees.pmtiles
