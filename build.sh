export $(grep -v '^#' .env 2>/dev/null || printenv | grep -v '^#' | xargs)
make install
psql -a -d $DATABASE_URL -f database.sql