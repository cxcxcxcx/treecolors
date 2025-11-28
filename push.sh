# Update cache version in sw.js
NEW_VERSION="tree-map-v$(date +%Y%m%d-%H%M%S)"
sed -i "s/const CACHE_NAME = .*/const CACHE_NAME = '$NEW_VERSION';/" web/sw.js
echo "Updated sw.js cache to $NEW_VERSION"

rsync -avz --delete \
 web/ \
 root@example.com:/var/www/fall_colors/ \
#  --dry-run
 