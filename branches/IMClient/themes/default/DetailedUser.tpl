<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=UTF-8">
	<style>
body{
	background-image: url('pwytter://theme/images/stripes.png');
}
.cmd{
	cursor: pointer;
}
a.name{
	font-weight: bold;
	text-decoration: none;
	color: black;
}
a.name:hover{
	font-weight: bold;
	text-decoration: underline;
	color: black;
}
a.service{
	text-decoration: underline;
	color: black;
}
	</style>
</head>
<body>
<table cellspacing="0"  style="background-image: url('pwytter://theme/images/bg.png');margin: 5;" width="100%">
	<tr><td width="30">
		<img src="[% var User['Image'] %]">
	</td><td>
		<b> [% var User['Name'] %]</b>
		 on <a class="service" href="[% var User['Url'] %]">[% var User['Service'] %]</a><br>
		<span style="font-size: small;">
			[%if User["CanReply"]%]
				<u class='cmd' onclick='window.pwytter.reply([% var User["Id"]%])'>reply</u>
			[%endif%]
			[%if User["CanReply"]%][%if User["CanSendDirectMessage"]%]
				|
			[%endif%][%endif%]
			[%if User["CanSendDirectMessage"]%]
				<u class='cmd' onclick='window.pwytter.direct([% var User["Id"]%])'>direct message</u>
			[%endif%]
		</span>
	</td></tr>
	<tr><td colspan="2">
	<b>Description:</b><br>
		[% var User['Description'] %]
	<td>
</table>
</body>
</html>
