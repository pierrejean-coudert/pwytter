<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=UTF-8">
	<style>
body{
	background-image: url('pwytter://image/theme/stripes.png');
}
	</style>
</head>
<body>
{foreach}
<table cellspacing="0"  style="background-image: url('pwytter://image/theme/bg.png');margin: 5;" width="100%">
	<tr><td width="30">
	<img src="{img}">
	</td><td>
	<b>{name}</b> {message}<br>
	<i style="font-size: small;">On {date}.</i>
	</td></tr>
</table>
{foreach}
<br>
<a href="{prev}">prev page</a> | <a href="{next}">next page</a>
</body>
</html>
