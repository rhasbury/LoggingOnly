<?php
$servername = "localhost";
$username = "monitor";
$password = "password";
$dbname = "temps";

//$con = new mysqli($servername, $username, $password, $dbname);

$con = mysql_connect($servername, $username, $password, $dbname);

if (!$con) {
  die('Could not connect: ' . mysql_error());
}

//mysql_select_db("temps", $con);

//$sql = "Select Month(`tdate`), Day(`tdate`), avg(`temperature`) AS 'avgtemp' from tempdat where `tdate` between '2015-04-01' and '2015-05-31' group by Month(`tdate`), Day(`tdate`)";
//$sql = "SELECT tdate, temperature1, temperature2, temperature3 FROM ltempdat ORDER BY tdate DESC LIMIT 2000";
//$sql = "SELECT DATE_FORMAT(timestamp_value, '%Y-%m-%d') as timestamp_value, SUM(traffic_count) as traffic_count FROM foot_traffic WHERE timestamp_value LIKE '2013-02%' GROUP BY DATE_FORMAT(timestamp_value, '%Y-%m-%d')";



if (isset($_GET["dateParam"])) {
	$date = ($_GET["dateParam"]) . '%';	
	//$sql = "SELECT n_lat, w_long, date_time, speed, altitude, mode, track, climb, enginetemp, ambienttemp FROM gps WHERE gps tdate LIKE " . "'" . $date . "'";
	$sql = "SELECT n_lat, w_long, date_time, speed, altitude, mode, track, climb, enginetemp, ambienttemp FROM temps.gps WHERE date_time LIKE " . "'" . $date . "'";
	error_log($sql, 0);
	$result = mysql_query($sql);
	
	// Creates the Document.
	$dom = new DOMDocument('1.0', 'UTF-8');
	$gpx = $dom->createElement('gpx');
	$gpx = $dom->appendChild($gpx);
	
	$gpx_version = $dom->createAttribute('version');
	$gpx->appendChild($gpx_version);
	$gpx_version_text = $dom->createTextNode('1.0');
	$gpx_version->appendChild($gpx_version_text);
	 
	$gpx_creator = $dom->createAttribute('creator');
	$gpx->appendChild($gpx_creator);
	$gpx_creator_text = $dom->createTextNode('http://thydzik.com');
	$gpx_creator->appendChild($gpx_creator_text);
	 
	$gpx_xmlns_xsi = $dom->createAttribute('xmlns:xsi');
	$gpx->appendChild($gpx_xmlns_xsi);
	$gpx_xmlns_xsi_text = $dom->createTextNode('http://www.w3.org/2001/XMLSchema-instance');
	$gpx_xmlns_xsi->appendChild($gpx_xmlns_xsi_text);
	 
	$gpx_xmlns = $dom->createAttribute('xmlns');
	$gpx->appendChild($gpx_xmlns);
	$gpx_xmlns_text = $dom->createTextNode('http://www.topografix.com/GPX/1/0');
	$gpx_xmlns->appendChild($gpx_xmlns_text);
	 
	$gpx_xsi_schemaLocation = $dom->createAttribute('xsi:schemaLocation');
	$gpx->appendChild($gpx_xsi_schemaLocation);
	$gpx_xsi_schemaLocation_text = $dom->createTextNode('http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd');
	$gpx_xsi_schemaLocation->appendChild($gpx_xsi_schemaLocation_text);
	 

	
	// Creates the root KML element and appends it to the root document
	//$node = $dom->createElementNS('http://earth.google.com/kml/2.1', 'kml');
	//$parNode = $dom->appendChild($node);
	
	// Creates a KML Document element and append it to the KML element.
	//$dnode = $dom->createElement('Document');
	//$docNode = $parNode->appendChild($dnode);
	

	
	// Iterates through the MySQL results, creating one Placemark for each row.
	error_log("beforeloop");
	
	$trkNode = $dom->createElement('trk');
	$gpx->appendChild($trkNode);
	$trksegNode = $dom->createElement('trkseg');
	$trkNode->appendChild($trksegNode);
	
	while ($row = @mysql_fetch_array($result))
	{
		  // Creates a Placemark and append it to the Document.

		  //$node = $dom->createElement('Placemark');
		  //$placeNode = $docNode->appendChild($node);

		  // Creates an id attribute and assign it the value of id column.
		  //$placeNode->setAttribute('id', 'placemark' . $row['id']);

		  // Create name, and description elements and assigns them the values of the name and address columns from the results.
		  //$nameNode = $dom->createElement('name',htmlentities($row['name']));
		  //$placeNode->appendChild($nameNode);
		  //$descNode = $dom->createElement('description', $row['address']);
		  //$placeNode->appendChild($descNode);
		  //$styleUrl = $dom->createElement('styleUrl', '#' . $row['type'] . 'Style');
		  //$placeNode->appendChild($styleUrl);
		  //error_log($row['date']);
		  //error_log("looooped");
		  // Creates a Point element.
		  //$pointNode = $dom->createElement('Point');
		  //$docNode->appendChild($pointNode);


		  // Creates a coordinates element and gives it the value of the lng and lat columns from the results.
		  $coorStr = $row['w_long'] . ','  . $row['n_lat'];
		  $coorLat = $dom->createAttribute('lat');
		  $coorLat->value = $row['n_lat'];
		  $coorLong = $dom->createAttribute('lon');
		  $coorLong->value = $row['w_long'];
		  $coorNode = $dom->createElement('trkpt');
		  $coorNode->appendChild($coorLat);
		  $coorNode->appendChild($coorLong);
		  
		  $trksegNode->appendChild($coorNode);
		  
	  
	  
	}
}
$kmlOutput = $dom->saveXML();
header('Content-type: application/vnd.google-earth.kml+xml');
echo $kmlOutput;
?>
	
	
	
	