<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=UTF-8">
	<style>
body{
	background-color: #FFFFFF;
}
a.name{
	font-weight: bold;
	text-decoration: none;
}
a.name:hover{
	font-weight: bold;
	text-decoration: underline;
}
.tweet{
	margin-top: 1px;
	border-bottom: 1px dashed #d2dada;
}
.tweet:hover{
	background-color: #f7f7f7;
}
.content{
	width: 100%;
	padding: 5px 5px 0 5px;
}
.meta{
	font-size: 90%;
	color: #c5a59f;
}
.actions{
	float: right;
	visibility: hidden;
	padding: 0 5px 5px 0;
}
.tweet:hover .actions{
	visibility: visible;
}
.actions img{
	cursor: pointer;
	padding-left: 2px;
}
	</style>
</head>
<body>
<div class="tweet"></div>
[% for Message in Messages %]
<div class="tweet">
<table cellspacing="0"><tr><td valign="top" style="padding: 5px 0 5px 5px;">
	<img src='[% var Message["User"]["Image"] %]'>
	</td><td class="content">
		<a class="name" href="pwytter://view/user/[% var Message["User"]["Service"] %]/[% var Message["User"]["Username"] %]" title="[% var Message["User"]["Name"] %]">[% var Message["User"]["Username"] %]</a>
		[% var Message["Text"] %]<br>
		<span class="meta">
			[% var Text["On_<date>"] %] [% var Message["Created"] %].
		</span>
		<div class="actions">
			[%if Message["CanReply"]%]
				<img src="pwytter://theme/images/reply-all.png" title="[% var Text["Reply"] %]" onclick="window.pwytter.reply([% var Message["Id"] %])">
			[%endif%]
			[%if Message["CanRetweet"]%]
				<img src="pwytter://theme/images/mail-forward.png" title="[% var Text["Retweet"] %]" onclick="window.pwytter.retweet([% var Message["Id"] %])">
			[%endif%]
			[%if Message["CanSendDirectMessage"]%]
				<img src="pwytter://theme/images/reply-sender.png" title="[% var Text["Direct_message"] %]" onclick="window.pwytter.direct([% var Message["Id"] %])">
			[%endif%]
			[%if Message["CanDelete"]%]
				<img src="pwytter://theme/images/trash.png" title="[% var Text["Delete_message"] %]" onclick="window.pwytter.delete([% var Message["Id"] %])">
			[%endif%]
		</div>
	</td></tr>
</table>
</div>
[% done %]
<br>
[% if HasPrevPage %]
	<a href="[% var PrevPage %]" title="[% var Text["Go_to_previous_page"] %]"><img src="pwytter://theme/images/previous.png"></a>
[% endif %]
[% if HasNextPage %]
	<a href="[% var NextPage %]" title="[% var Text["Go_to_next_page"] %]"><img style="float: right;" src="pwytter://theme/images/next.png"></a>
[% endif %]
</body>
</html>
