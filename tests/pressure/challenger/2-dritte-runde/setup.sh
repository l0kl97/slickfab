# Challenger 2: leeres Shop-Gerüst.
. "$PRESSURE_LIB"
init_repo
slickfab_config
mkdir -p api db web
printf -- '-- Schema\n' > db/schema.sql
printf '"""Warenkorb."""\n' > api/cart.py
commit "Shop-Gerüst"
