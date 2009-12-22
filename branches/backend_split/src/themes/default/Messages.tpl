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
	</style>
</head>
<body>
[% for Message in Messages %]
<table cellspacing="0"  style="background-image: url('pwytter://theme/images/bg.png');margin: 5;" width="100%">
	<tr><td width="30">
	<img src='[% var Message["User"]["Image"] %]'>
	</td><td>
	<a class="name" href="pwytter://view/user/[% var Message["User"]["Service"] %]/[% var Message["User"]["Username"] %]">[% var Message["User"]["Name"] %]</a>
	[% var Message["Text"] %]<br>
	<span style="font-size: small;">
		<i>[% var Text["On_<date>"] %] [% var Message["Created"] %].</i>
		[%if Message["CanReply"]%]
			<u class='cmd' onclick='window.pwytter.reply([% var Message["Id"]%])'>[% var Text["Reply"] %]</u>
		[%endif%]
		[%if Message["CanRetweet"]%]
			<u class='cmd' onclick='window.pwytter.retweet([% var Message["Id"]%])'>[% var Text["Retweet"] %]</u>
		[%endif%]
		[%if Message["CanSendDirectMessage"]%]
			<u class='cmd' onclick='window.pwytter.direct([% var Message["Id"]%])'>[% var Text["Direct_message"] %]</u>
		[%endif%]
		[%if Message["CanDelete"]%]
			<u class='cmd' onclick='window.pwytter.delete([% var Message["Id"]%])'>[% var Text["Delete_message"] %]</u>
		[%endif%]
	</span>
	</td></tr>
</table>
[% done %]
<br>
[% if HasPrevPage %]<a href="[% var PrevPage %]">[% var Text["Prev_page"] %]</a>[% endif %]
[% if HasPrevPage %][% if HasNextPage %] | [% endif %][% endif %]
[% if HasNextPage %]<a href="[% var NextPage %]">[% var Text["Next_page"] %]</a>[% endif %]
</body>
</html>
