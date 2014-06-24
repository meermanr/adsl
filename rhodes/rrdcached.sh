#!/bin/bash
exec rrdcached -g -l unix:./rrdcached.sock -p rrdcached.pid
