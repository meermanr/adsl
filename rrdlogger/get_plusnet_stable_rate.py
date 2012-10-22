#!/usr/bin/env python
# vim: set expandtab autoindent tabstop=4 softtabstop=4 shiftwidth=4:
import config

def get_ip_profile():
    import os
    import sys
    import subprocess as sp

    base_cmd = [
            "curl", "https://portal.plus.net/my.html?action=stable_rate",
            "--data", "username={0}&authentication_realm=portal.plus.net&password={1}&x=21&y=15".format(
                config.plusnet_user, config.plusnet_pass),
            "--silent",
            ]

    os.chdir( os.path.dirname( __file__ ) )

    if os.path.exists("cookiejar"):
        os.unlink("cookiejar")

    # Once to get a session cookie (stored in ./cookiejar)
    new_cmd = base_cmd + ["--cookie-jar", "./cookiejar"]
    with file(os.devnull, "w+b") as fh:
        ph = sp.Popen(
                new_cmd,
                stdin=fh,
                stdout=fh,
                stderr=fh,
                shell=False,
                )
        ph.wait()

    # And again with cookies obtained in previous step
    new_cmd = base_cmd + ["--cookie", "./cookiejar"]
    with file(os.devnull, "w+b") as fh:
        ph = sp.Popen(
                new_cmd,
                stdin=fh,
                stdout=sp.PIPE,
                stderr=fh,
                shell=False,
                )
        html = ph.stdout.read()
        ph.wait()

    import re
    for section in re.split("</?dl>", html):
        if "Current line speed:" in section:
            for item in section.split("<dt>"):
                if "</dt>" not in item:
                    continue

                key, value = item.split("</dt>")
                key = key.strip()
                if key != "Current line speed:":
                    continue

                value = re.sub("<.*?>", "", value)
                value = value.strip()
                # E.g. "3.5 Mb"
                if " Mb" in value:
                    return int( float(value[:-len(" Mb")]) * 1000 )
            break
    else:
        raise Exception("Current line speed not present, script may need updating.")

if __name__ == "__main__":
    try:
        print get_ip_profile()
    except:
        print "U"
        raise
