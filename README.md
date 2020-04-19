# Phishing de credenciales en logins de portales cautivos

Se necesita: 
- dnsmasq
- hostapd
- macchanger
- apache2
- gnome-terminal

Uso:

- Introducir el html del login para hacer phishing en captive, con una estructura de 
  usuario y contraseña similar a la de index.html
- Cambiar el nombre de la wifi en run.sh
- Crear la siguiente base de datos:
```
service mysql start
mysql
MariaDB [(none)]> create database fakeap;
MariaDB [(none)]> create user user;
MariaDB [(none)]> grant all on fakeap.* to 'user'@'localhost' identified by 'password';
MariaDB [(none)]> use fakeap
MariaDB [fakeap]> create table accounts(email varchar(30), password varchar(30));
MariaDB [fakeap]> ALTER DATABASE fakeap CHARACTER SET 'utf8';
MariaDB [fakeap]> select * from accounts;
```

Cómo funciona este script:

	1.  Crea un punto de acceso wi-fi

	2.  Crea un servidor DHCP y uno DNS que redirecciona todo a un servidor Apache2 con 
	    el html del phishing

	3.  Cuando un dispositivo se conecta, éste comprueba la calidad de la conexión, enviando
	    un get request a alguna de las páginas por defecto como 
	    connectivitycheck.gstatic.com/generate_204.

	3.1 Si hay conexión a Internet:
	    Iptables redirige las requests a la máquina y ésta responde (mod_rewrite) con código 302 
	    apuntando al servidor Apache (a sí mismo), indicando a TODOS los dispotivos que es ahi 
	    donde está el portal cautivo.

	3.2 Si no hay conexión a Internet: 
	    Dnsmasq redirige las requests a la máquina y ésta (mod_rewrite) responde con código 302 
	    apuntando al servidor Apache (a sí mismo). Sin embargo,por este método, los dispositivos 
	    Samsung no consiguen llegar al servidor del portal cautivo, porque de algún modo 
	    necesitan conexión a Internet para comunicarse con algún servidor (está por investigar)
