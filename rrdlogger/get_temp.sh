#!/bin/bash
curl --silent http://www.cl.cam.ac.uk/research/dtg/weather/current-obs.txt | sed -ne 's/^Temperature:\s*\([0-9.]*\).*/\1/p'
