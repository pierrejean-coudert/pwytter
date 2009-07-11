<html>
<head>
	<meta http-equiv="content-type" content="text/html; charset=UTF-8">
</head>
<body>
<ul>
[% for User in Users %]
	<li>[% var User['Name'] %] on [% var User['Service'] %], <b onclick="window.pwytter.reply([% var User['Id'] %])">reply</b></li>
[% done %]
</ul>
<br>
[% if HasPrevPage %]<a href="[% var PrevPage %]">prev page</a>[% endif %]
[% if HasPrevPage %][% if HasNextPage %] | [% endif %][% endif %]
[% if HasNextPage %]<a href="[% var NextPage %]">next page</a>[% endif %]
</body>
</html>
