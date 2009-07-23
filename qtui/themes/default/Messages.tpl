<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=UTF-8">
	<style>
body{
	background-image: url('pwytter://image/theme/stripes.png');
}
.reply{
	cursor: pointer;
}
	</style>
</head>
<body>
[% for Message in Messages %]
<div style="border-bottom:1px solid #ddd">
<table cellspacing="0"  style="background-image: url('pwytter://image/theme/bg.png');margin: 5;" width="100%">
	<tr><td width="30">
	<img src='[% var Message["User"]["Image"] %]'>
	</td><td>
	<b>[% var Message["User"]["Name"] %]</b> [% var Message["Text"] %]<br>
	<i style="font-size: small;">On [% var Message["Created"] %].</i>
	[%if Message["User"]["CanReply"]%]
		<u class='reply' onclick='window.pwytter.reply([% var Message["Id"]%])'>reply</u>
	[%endif%]
	</td></tr>
</table>
</div>
[% done %]
<br>
[% if HasPrevPage %]<a href="[% var PrevPage %]">prev page</a>[% endif %]
[% if HasPrevPage %][% if HasNextPage %] | [% endif %][% endif %]
[% if HasNextPage %]<a href="[% var NextPage %]">next page</a>[% endif %]
</body>
</html>
