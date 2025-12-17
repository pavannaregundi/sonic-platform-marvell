#!/bin/bash


case "$(cat /proc/cmdline)" in
*SONIC_BOOT_TYPE=warm*|*SONIC_BOOT_TYPE=fast*)
   ;;
*)
    # SFP Re-timer Settings
    /usr/local/bin/d64p512t-retimer.sh

    # JA Settings
    /usr/local/bin/d64p512t-ja.sh

    # Bring OSFP out-of-reset
    i2cset -f -y 1 0x41 0x30 0x0 0x0 0x0 0x0 i
    i2cset -f -y 1 0x45 0x30 0x0 0x0 0x0 0x0 i

    # Set LPMODE to off - OSFP
    i2cset -f -y 1 0x41 0x34 0xff 0xff 0xff 0xff i
    i2cset -f -y 1 0x45 0x34 0xff 0xff 0xff 0xff i
esac

exit 0
