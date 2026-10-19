#!/usr/bin/env bash
# Wave 0d: fetch datasheets for the active parts into CLAUDE_REVIEW/datasheets/.
# Vendors that block scripted download are reported so they can be fetched by hand.
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/datasheets"
mkdir -p "$DIR"
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36'
get() { # get <name> <url>
  local f="$DIR/$1.pdf"
  [ -s "$f" ] && { echo "SKIP  $1 (have it)"; return; }
  curl -sSL -A "$UA" --max-time 60 -o "$f" "$2" || true
  if [ -s "$f" ] && [ "$(file -b --mime-type "$f")" = application/pdf ]; then
    echo "OK    $1  $(du -h "$f"|cut -f1)"
  else
    rm -f "$f"; echo "FAIL  $1  <- $2"
  fi
}
get LT3074_LDO              "https://www.analog.com/media/en/technical-documentation/data-sheets/lt3074.pdf"
get MAX6373_watchdog        "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6369-MAX6374.pdf"
get PAC1944_power_monitor   "https://ww1.microchip.com/downloads/en/DeviceDoc/PAC194X-5X-Family-Data-Sheet-DS20006539.pdf"
get AD5272_digipot          "https://www.analog.com/media/en/technical-documentation/data-sheets/AD5272_5274.pdf"
get PCA9306_lvl_translator  "https://www.ti.com/lit/ds/symlink/pca9306.pdf"
get 74LVC1G175_dff          "https://www.ti.com/lit/ds/symlink/sn74lvc1g175.pdf"
get 74LVC1G08_and           "https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf"
get MMBT3904_npn            "https://www.onsemi.com/pdf/datasheet/pzt3904-d.pdf"
echo; ls -la "$DIR"
