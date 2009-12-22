<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=UTF-8">
	<style>
.cmd{
	cursor: pointer;
}
a.name{
	font-weight: bold;
	text-decoration: none;
}
a.name:hover{
	font-weight: bold;
	text-decoration: underline;
}
a.service{
	text-decoration: none;
	color: black;
}
a.service:hover{
	text-decoration: underline;
	color: black;
}
table:first-child{
	border-top: 1 px solid #eeeeee;
}
td{
	padding: 5px;
	border-bottom: 1 px solid #eeeeee;
}
.odd{
	background-color: #f9f9f9;
}
.even{
	background-color: #ffffff;
}
.odd:hover, .even:hover{
	background-color: #eeeeee;
}
.content{
	width: 100%;
}
.actions{
	float: right;
	visibility: hidden;
	padding: 0 5px 5px 0;
}
.odd:hover .actions, .even:hover .actions{
	visibility: visible;
}
.actions img{
	cursor: pointer;
	padding-left: 2px;
}
.meta{
	font-size: 90%;
	color: #c5a59f;
}
	</style>
	<script>
function CreateAlternateTable(){
	var table = document.getElementById('alternateTable')
	for(var i = 0; i < table.rows.length; i++){
		if(i % 2 == 0)
			table.rows[i].className = "odd";
		else
			table.rows[i].className = "even";
	}
}
	</script>
</head>
<body onload="CreateAlternateTable()">
<table cellspacing="0" id="alternateTable">
	<tr><td valign="top" style="padding: 5px 0 5px 5px;">
		<img src="[% var User['Image'] %]">
	</td><td class="content">
		<a class="name" href="pwytter://view/user/[% var User["Service"] %]/[% var User["Username"] %]" title="[% var User["Name"] %]">[% var User["Username"] %]</a>
		[% var Text["<user>_on_<service>"] %] <a class="service" href="[% var User['Url'] %]">[% var User['Service'] %]</a><br>
		[% var User["Name"] %] | [% var User["Location"] %]<br>
		<span class="meta">
			[% var User["Description"] %].
		</span>
		<div class="actions">
			[%if User["CanReply"]%]
				<img src="pwytter://theme/images/reply-all.png" title="[% var Text["Reply"] %]" onclick="window.pwytter.reply([% var User["Id"] %])">
			[%endif%]
			[%if User["CanSendDirectMessage"]%]
				<img src="pwytter://theme/images/reply-sender.png" title="[% var Text["Direct_message"] %]" onclick="window.pwytter.direct([% var User["Id"] %])">
			[%endif%]
		</div>
	</td></tr>
</table>
</body>
</html>
