<a href='now.php'>Query ADSL Sync rates now</a>
<?php
$graphs = array();
$graphs[] = array( "ADSL", "--lower-limit=0 \
    DEF:sync_down_kbps=adsl.rrd:sync_down:MIN \
	DEF:ip_profile_kbps=adsl.rrd:ip_profile:MIN \
	DEF:gw_ping_ms=adsl.rrd:gw_ping:MIN \
    \
	CDEF:sync_down=sync_down_kbps,1000,* \
	CDEF:ip_profile=ip_profile_kbps,1000,* \
	CDEF:gw_ping=gw_ping_ms,50000,* \
    \
	AREA:sync_down#ffcc99:'ADSL Downstream (bits/second)' \
	LINE:ip_profile#009900:'IP Profile (bits/second)' \
	LINE:gw_ping#cc0000:'Gateway Latency (1.0M == 20ms)' \
");

$periods = array(
	# Name, Start, end
	array("Last 2 hours", "now - 2 hours", "now"),
	array("Today", "00:00", "23:59"),
	array("Yesterday", "00:00 - 24 hours", "23:59 - 24 hours"),
	array("This week", "00:00 Monday", "00:00 Monday + 1 week"),
	array("Last week", "00:00 Monday - 1 week", "00:00 Monday"),
	array("Last 4 weeks", "now - 4 week", "now"),
	array("Last 6 months", "now - 6 months", "now"),
);

foreach( $periods as $period )
{
	list($p_name, $p_start, $p_end) = $period;

	print "<h1>$p_name</h1>";

	foreach( $graphs as $graph )
	{
		list($title, $def) = $graph;

		$safe_title = str_replace(" ", "_", $title);
		$safe_period = str_replace(" ", "_", $p_name);

		$filename = "images/g_${safe_title}_${safe_period}.png";

		system("
			rrdtool graph $filename \
			--start '$p_start' \
			--end '$p_end' \
			--title '$title' \
			--width 800 \
			--height 100 \
			--imgformat PNG \
			$def \
			2>&1 1>/dev/null");

		print "<img src='$filename' />";
	}
}
