<?php
    $username = "monitor"; 
    $password = "password";   
    $host = "localhost";
    $database="temps";
    
    $server = mysql_connect($host, $username, $password);
    $connection = mysql_select_db($database, $server);

//    $myquery = "
//SELECT  `date`, `close` FROM  `data2`
//";

$date = '2015-09-11';

    $myquery = "
SELECT  `fix_time`, `enginetemp`, `ambienttemp` FROM  `gps` WHERE fix_time LIKE " . "'" . $date . "%'" . " ORDER by fix_time DESC LIMIT 3000
";

	error_log($myquery , 0);
    $query = mysql_query($myquery);
    
    if ( ! $query ) {
        echo mysql_error();
        die;
    }
    
    $data = array();
    
    for ($x = 0; $x < mysql_num_rows($query); $x++) {
        $data[] = mysql_fetch_assoc($query);
    }
    
    echo json_encode($data);     
     
    mysql_close($server);
?>